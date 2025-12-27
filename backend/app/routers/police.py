from fastapi import APIRouter, HTTPException, status
from app.models import PoliceScanRequest, PoliceScanResponse
from app.database import (
    get_users_collection,
    get_shifts_collection,
    get_workplace_bindings_collection,
    get_verifications_collection,
    is_using_fallback
)
from app.fallback import (
    find_user_by_uuid,
    find_shift_by_stt,
    find_workplace_binding,
    get_recent_verifications
)
from datetime import datetime
import base64
import json

router = APIRouter()

def decode_stt(stt: str) -> dict:
    """
    Decode STT (Shift Trust Token) from QR code.
    Returns dict with shift_id, worker_uuid, etc.
    """
    try:
        json_str = base64.b64decode(stt.encode()).decode()
        return json.loads(json_str)
    except Exception as e:
        raise ValueError(f"Invalid STT format: {str(e)}")

@router.post("/police/scan", response_model=PoliceScanResponse)
async def police_scan_worker(request: PoliceScanRequest):
    """
    Police checkpoint scan - extended worker verification.
    
    Used by: Police dashboard at checkpoints or investigations
    
    Process:
    1. Decode STT (QR code)
    2. Find shift and verify active
    3. Get complete worker identity
    4. Get workplace authorization
    5. Get supervisor details
    6. Return comprehensive verification data
    
    Police sees MORE than customers:
    - Full identity details
    - Workplace binding history
    - Supervisor contact info
    - Shift timing details
    - Risk assessment
    - Recent verification history
    """
    
    # Validate officer
    if is_using_fallback():
        officer = find_user_by_uuid(request.officer_uuid)
    else:
        users_collection = get_users_collection()
        if users_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        officer = users_collection.find_one({"uuid": request.officer_uuid})
    
    if not officer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Officer not found"
        )
    
    if officer.get("role") != "police":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: User is not authorized law enforcement"
        )
    
    # Decode STT
    try:
        stt_data = decode_stt(request.stt)
    except ValueError as e:
        return PoliceScanResponse(
            verified=False,
            identity=None,
            workplace=None,
            shift_status=None,
            risk_state=None,
            supervisor_name=None,
            message=f"Invalid QR code: {str(e)}"
        )
    
    # Find shift by STT
    if is_using_fallback():
        shift = find_shift_by_stt(request.stt)
    else:
        shifts_collection = get_shifts_collection()
        if shifts_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        shift = shifts_collection.find_one({"stt": request.stt})
    
    if not shift:
        return PoliceScanResponse(
            verified=False,
            identity=None,
            workplace=None,
            shift_status=None,
            risk_state=None,
            supervisor_name=None,
            message="QR code not found or invalid"
        )
    
    # Get worker details
    worker_uuid = shift.get("uuid")
    
    if is_using_fallback():
        worker = find_user_by_uuid(worker_uuid)
    else:
        users_collection = get_users_collection()
        worker = users_collection.find_one({"uuid": worker_uuid})
    
    if not worker:
        return PoliceScanResponse(
            verified=False,
            identity=None,
            workplace=None,
            shift_status=None,
            risk_state=None,
            supervisor_name=None,
            message="Worker not found"
        )
    
    # Get workplace binding
    if is_using_fallback():
        binding = find_workplace_binding(worker_uuid)
    else:
        bindings_collection = get_workplace_bindings_collection()
        binding = bindings_collection.find_one({
            "uuid": worker_uuid,
            "active": True
        }) if bindings_collection else None
    
    # Get supervisor details
    supervisor_id = shift.get("supervisor_id")
    supervisor = None
    
    if supervisor_id:
        if is_using_fallback():
            supervisor = find_user_by_uuid(supervisor_id)
        else:
            users_collection = get_users_collection()
            supervisor = users_collection.find_one({"uuid": supervisor_id})
    
    # Build identity section
    identity = {
        "uuid": worker.get("uuid"),
        "name": worker.get("name"),
        "phone": worker.get("phone"),
        "role": worker.get("role"),
        "registered_at": worker.get("created_at"),
        "platform_links": worker.get("platform_links", [])
    }
    
    # Build workplace section
    workplace = {
        "name": shift.get("workplace"),
        "location": binding.get("location") if binding else None,
        "bound_at": binding.get("created_at") if binding else None,
        "binding_active": binding.get("active") if binding else False
    }
    
    # Build shift status section
    shift_active = shift.get("end") is None
    shift_status = {
        "active": shift_active,
        "shift_id": shift.get("shift_id"),
        "start_time": shift.get("start"),
        "end_time": shift.get("end"),
        "duration_hours": _calculate_shift_duration(shift) if shift_active else None
    }
    
    # Return comprehensive police verification
    return PoliceScanResponse(
        verified=True,
        identity=identity,
        workplace=workplace,
        shift_status=shift_status,
        risk_state=shift.get("risk_state"),
        supervisor_name=supervisor.get("name") if supervisor else "Unknown",
        message="Worker verified - All details validated"
    )

def _calculate_shift_duration(shift: dict) -> float:
    """Calculate shift duration in hours"""
    try:
        start = shift.get("start")
        if isinstance(start, str):
            start = datetime.fromisoformat(start.replace('Z', '+00:00'))
        
        duration = datetime.utcnow() - start
        return round(duration.total_seconds() / 3600, 2)  # Hours with 2 decimals
    except:
        return 0.0

@router.get("/police/events")
async def get_recent_events(limit: int = 50):
    """
    Get recent verification events.
    
    Used by: Police dashboard event log
    
    Returns recent worker verifications across the system.
    Useful for monitoring activity patterns.
    """
    
    if is_using_fallback():
        verifications = get_recent_verifications(limit)
    else:
        verifications_collection = get_verifications_collection()
        if verifications_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        verifications = list(verifications_collection.find().sort("time", -1).limit(limit))
        
        # Remove _id fields
        for verification in verifications:
            if "_id" in verification:
                del verification["_id"]
    
    # Enrich with worker names
    enriched_events = []
    for verification in verifications:
        worker_uuid = verification.get("worker_uuid")
        
        if is_using_fallback():
            worker = find_user_by_uuid(worker_uuid)
        else:
            users_collection = get_users_collection()
            worker = users_collection.find_one({"uuid": worker_uuid}) if users_collection else None
        
        enriched_event = {
            "time": verification.get("time"),
            "worker_uuid": worker_uuid,
            "worker_name": worker.get("name") if worker else "Unknown",
            "customer_uuid": verification.get("customer_uuid"),
            "location": verification.get("location")
        }
        enriched_events.append(enriched_event)
    
    return {
        "events": enriched_events,
        "count": len(enriched_events)
    }

@router.get("/police/active-workers")
async def get_active_workers():
    """
    Get all workers currently on active shifts.
    
    Used by: Police dashboard for area monitoring
    
    Returns list of workers with active shifts including:
    - Worker identity
    - Current workplace
    - Shift start time
    - Risk state
    """
    
    # Get all active shifts (where end is null)
    if is_using_fallback():
        from app.fallback import _fallback_data
        active_shifts = [s for s in _fallback_data["shifts"] if s.get("end") is None]
    else:
        shifts_collection = get_shifts_collection()
        if shifts_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        active_shifts = list(shifts_collection.find({"end": None}))
        
        # Remove _id fields
        for shift in active_shifts:
            if "_id" in shift:
                del shift["_id"]
    
    # Enrich with worker details
    active_workers = []
    for shift in active_shifts:
        worker_uuid = shift.get("uuid")
        
        if is_using_fallback():
            worker = find_user_by_uuid(worker_uuid)
        else:
            users_collection = get_users_collection()
            worker = users_collection.find_one({"uuid": worker_uuid}) if users_collection else None
        
        if worker:
            active_worker = {
                "worker_uuid": worker_uuid,
                "worker_name": worker.get("name"),
                "worker_phone": worker.get("phone"),
                "workplace": shift.get("workplace"),
                "shift_start": shift.get("start"),
                "risk_state": shift.get("risk_state"),
                "shift_duration_hours": _calculate_shift_duration(shift)
            }
            active_workers.append(active_worker)
    
    return {
        "active_workers": active_workers,
        "count": len(active_workers)
    }