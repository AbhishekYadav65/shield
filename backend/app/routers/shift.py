from fastapi import APIRouter, HTTPException, status
from app.models import ShiftStartRequest, ShiftEndRequest, ShiftStatusResponse, RiskState
from app.database import (
    get_users_collection,
    get_workplace_bindings_collection,
    get_shifts_collection,
    is_using_fallback
)
from app.fallback import (
    find_user_by_uuid,
    find_workplace_binding,
    insert_shift,
    find_active_shift,
    find_shift_by_id,
    update_shift
)
from app.risk_engine import calculate_risk_score, get_risk_state
from datetime import datetime
import uuid
import json
import base64

router = APIRouter()

def generate_stt(shift_id: str, worker_uuid: str, workplace: str, start_time: datetime) -> str:
    """
    Generate Shift Trust Token (STT) - the QR code data.
    
    STT contains:
    - shift_id: unique shift identifier
    - worker_uuid: who is working
    - workplace: where they're working
    - start_time: when shift started
    - issued_at: token generation time
    
    In production, this would be cryptographically signed.
    For MVP, we encode as base64 JSON.
    """
    stt_data = {
        "shift_id": shift_id,
        "worker_uuid": worker_uuid,
        "workplace": workplace,
        "start_time": start_time.isoformat(),
        "issued_at": datetime.utcnow().isoformat()
    }
    
    # Convert to JSON then base64
    json_str = json.dumps(stt_data)
    stt = base64.b64encode(json_str.encode()).decode()
    
    return stt

def decode_stt(stt: str) -> dict:
    """
    Decode STT back to data.
    Returns dict with shift_id, worker_uuid, etc.
    """
    try:
        json_str = base64.b64decode(stt.encode()).decode()
        return json.loads(json_str)
    except Exception as e:
        raise ValueError(f"Invalid STT format: {str(e)}")

@router.post("/shift/start")
async def start_shift(request: ShiftStartRequest):
    """
    Start a new shift for a worker.
    
    Used by: Supervisor dashboard
    
    Process:
    1. Validate worker exists and is a worker role
    2. Validate supervisor exists and is a supervisor role
    3. Check worker has active workplace binding
    4. Check worker doesn't already have active shift
    5. Calculate initial risk score
    6. Generate STT (QR code data)
    7. Create shift record
    8. Return shift details with STT
    
    The STT is what the worker shows in their QR code.
    """
    
    # Validate worker
    if is_using_fallback():
        worker = find_user_by_uuid(request.worker_uuid)
    else:
        users_collection = get_users_collection()
        if users_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        worker = users_collection.find_one({"uuid": request.worker_uuid})
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )
    
    if worker.get("role") != "worker":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a worker"
        )
    
    # Validate supervisor
    if is_using_fallback():
        supervisor = find_user_by_uuid(request.supervisor_id)
    else:
        users_collection = get_users_collection()
        supervisor = users_collection.find_one({"uuid": request.supervisor_id})
    
    if not supervisor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supervisor not found"
        )
    
    if supervisor.get("role") != "supervisor":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a supervisor"
        )
    
    # Check workplace binding
    if is_using_fallback():
        binding = find_workplace_binding(request.worker_uuid)
    else:
        bindings_collection = get_workplace_bindings_collection()
        if bindings_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        binding = bindings_collection.find_one({
            "uuid": request.worker_uuid,
            "active": True
        })
    
    if not binding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Worker is not bound to any workplace. Bind worker first."
        )
    
    # Verify workplace matches
    if binding.get("workplace") != request.workplace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Worker is bound to {binding.get('workplace')}, not {request.workplace}"
        )
    
    # Check for existing active shift
    if is_using_fallback():
        existing_shift = find_active_shift(request.worker_uuid)
    else:
        shifts_collection = get_shifts_collection()
        if shifts_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        existing_shift = shifts_collection.find_one({
            "uuid": request.worker_uuid,
            "end": None
        })
    
    if existing_shift:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker already has an active shift"
        )
    
    # Calculate risk score
    risk_score = calculate_risk_score(
        worker_data=worker,
        current_time=datetime.utcnow(),
        location_zone=binding.get("location"),
        complaint_count=0  # TODO: Implement complaint tracking
    )
    risk_state = get_risk_state(risk_score)
    
    # Generate shift ID and STT
    shift_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    stt = generate_stt(shift_id, request.worker_uuid, request.workplace, start_time)
    
    # Create shift record
    shift_data = {
        "shift_id": shift_id,
        "uuid": request.worker_uuid,
        "start": start_time.isoformat(),
        "end": None,
        "stt": stt,
        "risk_state": risk_state.value,
        "workplace": request.workplace,
        "supervisor_id": request.supervisor_id
    }
    
    try:
        if is_using_fallback():
            success = insert_shift(shift_data)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create shift"
                )
        else:
            shifts_collection = get_shifts_collection()
            if shifts_collection is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database unavailable"
                )
            shifts_collection.insert_one(shift_data)
        
        return {
            "success": True,
            "message": f"Shift started for {worker.get('name')}",
            "shift": {
                "shift_id": shift_id,
                "worker_uuid": request.worker_uuid,
                "worker_name": worker.get("name"),
                "workplace": request.workplace,
                "supervisor_id": request.supervisor_id,
                "start": start_time.isoformat(),
                "stt": stt,
                "risk_state": risk_state.value
            }
        }
    
    except Exception as e:
        print(f"Shift start error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start shift: {str(e)}"
        )

@router.post("/shift/end")
async def end_shift(request: ShiftEndRequest):
    """
    End an active shift.
    
    Used by: Supervisor dashboard
    
    Process:
    1. Find shift by shift_id
    2. Validate supervisor has permission
    3. Set end time
    4. Update shift record
    """
    
    # Find shift
    if is_using_fallback():
        shift = find_shift_by_id(request.shift_id)
    else:
        shifts_collection = get_shifts_collection()
        if shifts_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        shift = shifts_collection.find_one({"shift_id": request.shift_id})
    
    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift not found"
        )
    
    # Check if already ended
    if shift.get("end") is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shift has already ended"
        )
    
    # Verify supervisor has permission
    if shift.get("supervisor_id") != request.supervisor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the supervising supervisor can end this shift"
        )
    
    # Update shift
    end_time = datetime.utcnow()
    update_data = {"end": end_time.isoformat()}
    
    try:
        if is_using_fallback():
            success = update_shift(request.shift_id, update_data)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to end shift"
                )
        else:
            shifts_collection = get_shifts_collection()
            if shifts_collection is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database unavailable"
                )
            shifts_collection.update_one(
                {"shift_id": request.shift_id},
                {"$set": update_data}
            )
        
        return {
            "success": True,
            "message": "Shift ended successfully",
            "shift_id": request.shift_id,
            "end_time": end_time.isoformat()
        }
    
    except Exception as e:
        print(f"Shift end error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end shift: {str(e)}"
        )

@router.get("/shift/status/{worker_uuid}", response_model=ShiftStatusResponse)
async def get_shift_status(worker_uuid: str):
    """
    Get current shift status for a worker.
    
    Used by: Worker dashboard (polled every 3 seconds)
    
    Returns:
    - active: boolean
    - shift details if active (shift_id, stt, risk_state, start_time, workplace)
    - null if no active shift
    
    This is what makes the worker QR code appear/disappear in real-time.
    """
    
    # Find active shift
    if is_using_fallback():
        shift = find_active_shift(worker_uuid)
    else:
        shifts_collection = get_shifts_collection()
        if shifts_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        shift = shifts_collection.find_one({
            "uuid": worker_uuid,
            "end": None
        })
    
    if not shift:
        return ShiftStatusResponse(
            active=False,
            shift_id=None,
            stt=None,
            risk_state=None,
            start_time=None,
            workplace=None
        )
    
    # Parse start time
    start_time = shift.get("start")
    if isinstance(start_time, str):
        try:
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        except:
            start_time = None
    
    return ShiftStatusResponse(
        active=True,
        shift_id=shift.get("shift_id"),
        stt=shift.get("stt"),
        risk_state=shift.get("risk_state"),
        start_time=start_time,
        workplace=shift.get("workplace")
    )