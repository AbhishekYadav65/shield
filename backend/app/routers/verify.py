from fastapi import APIRouter, HTTPException, status
from app.models import VerifyWorkerRequest, VerifyWorkerResponse
from app.database import (
    get_users_collection,
    get_shifts_collection,
    get_verifications_collection,
    is_using_fallback
)
from app.fallback import (
    find_user_by_uuid,
    find_shift_by_stt,
    insert_verification
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

@router.post("/verify/worker", response_model=VerifyWorkerResponse)
async def verify_worker(request: VerifyWorkerRequest):
    """
    Verify a worker by scanning their QR code (STT).
    
    Used by: Customer dashboard
    
    Process:
    1. Decode STT (QR code data)
    2. Find shift by STT
    3. Verify shift is active (end is null)
    4. Get worker details
    5. Get workplace details
    6. Log verification
    7. Return worker info + risk state
    
    Customer sees:
    - Worker name
    - Worker photo (hash reference)
    - Employer/workplace
    - Shift active status
    - Risk color (green/yellow/red)
    """
    
    # Validate customer
    if is_using_fallback():
        customer = find_user_by_uuid(request.customer_uuid)
    else:
        users_collection = get_users_collection()
        if users_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        customer = users_collection.find_one({"uuid": request.customer_uuid})
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    if customer.get("role") != "customer":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a customer"
        )
    
    # Decode STT
    try:
        stt_data = decode_stt(request.stt)
    except ValueError as e:
        return VerifyWorkerResponse(
            verified=False,
            worker_name=None,
            worker_photo=None,
            employer=None,
            shift_active=False,
            risk_color=None,
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
        return VerifyWorkerResponse(
            verified=False,
            worker_name=None,
            worker_photo=None,
            employer=None,
            shift_active=False,
            risk_color=None,
            message="QR code not found or invalid"
        )
    
    # Check if shift is active
    if shift.get("end") is not None:
        return VerifyWorkerResponse(
            verified=False,
            worker_name=None,
            worker_photo=None,
            employer=None,
            shift_active=False,
            risk_color=None,
            message="Worker's shift has ended"
        )
    
    # Get worker details
    worker_uuid = shift.get("uuid")
    
    if is_using_fallback():
        worker = find_user_by_uuid(worker_uuid)
    else:
        users_collection = get_users_collection()
        worker = users_collection.find_one({"uuid": worker_uuid})
    
    if not worker:
        return VerifyWorkerResponse(
            verified=False,
            worker_name=None,
            worker_photo=None,
            employer=None,
            shift_active=False,
            risk_color=None,
            message="Worker not found"
        )
    
    # Log verification
    verification_data = {
        "worker_uuid": worker_uuid,
        "customer_uuid": request.customer_uuid,
        "time": datetime.utcnow().isoformat(),
        "location": None  # TODO: Can add GPS location if needed
    }
    
    try:
        if is_using_fallback():
            insert_verification(verification_data)
        else:
            verifications_collection = get_verifications_collection()
            if verifications_collection:
                verifications_collection.insert_one(verification_data)
    except Exception as e:
        print(f"Verification logging error: {str(e)}")
        # Don't fail the verification if logging fails
    
    # Return worker info
    return VerifyWorkerResponse(
        verified=True,
        worker_name=worker.get("name"),
        worker_photo=worker.get("face_hash"),  # In production, return photo URL
        employer=shift.get("workplace"),
        shift_active=True,
        risk_color=shift.get("risk_state"),
        message="Worker verified successfully"
    )

@router.get("/verify/history/{customer_uuid}")
async def get_customer_verification_history(customer_uuid: str, limit: int = 20):
    """
    Get verification history for a customer.
    
    Used by: Customer profile page
    
    Returns list of workers the customer has verified.
    """
    
    # Validate customer
    if is_using_fallback():
        customer = find_user_by_uuid(customer_uuid)
    else:
        users_collection = get_users_collection()
        if users_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        customer = users_collection.find_one({"uuid": customer_uuid})
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Get verifications
    if is_using_fallback():
        from app.fallback import get_verifications_by_customer
        verifications = get_verifications_by_customer(customer_uuid)
        # Sort by time (most recent first)
        verifications.sort(key=lambda x: x.get("time", ""), reverse=True)
        verifications = verifications[:limit]
    else:
        verifications_collection = get_verifications_collection()
        if verifications_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        verifications = list(verifications_collection.find(
            {"customer_uuid": customer_uuid}
        ).sort("time", -1).limit(limit))
        
        # Remove _id fields
        for verification in verifications:
            if "_id" in verification:
                del verification["_id"]
    
    # Enrich with worker names
    enriched_verifications = []
    for verification in verifications:
        worker_uuid = verification.get("worker_uuid")
        
        if is_using_fallback():
            worker = find_user_by_uuid(worker_uuid)
        else:
            users_collection = get_users_collection()
            worker = users_collection.find_one({"uuid": worker_uuid}) if users_collection else None
        
        enriched_verification = {
            **verification,
            "worker_name": worker.get("name") if worker else "Unknown"
        }
        enriched_verifications.append(enriched_verification)
    
    return {
        "customer_uuid": customer_uuid,
        "verifications": enriched_verifications,
        "count": len(enriched_verifications)
    }

@router.get("/verify/stats/{worker_uuid}")
async def get_worker_verification_stats(worker_uuid: str):
    """
    Get verification statistics for a worker.
    
    Used by: Worker profile page
    
    Returns total verification count and recent verifications.
    """
    
    # Validate worker
    if is_using_fallback():
        worker = find_user_by_uuid(worker_uuid)
    else:
        users_collection = get_users_collection()
        if users_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        worker = users_collection.find_one({"uuid": worker_uuid})
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )
    
    # Get verification count
    if is_using_fallback():
        from app.fallback import get_verifications_by_worker
        verifications = get_verifications_by_worker(worker_uuid)
        total_count = len(verifications)
        recent_verifications = sorted(
            verifications,
            key=lambda x: x.get("time", ""),
            reverse=True
        )[:10]
    else:
        verifications_collection = get_verifications_collection()
        if verifications_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        total_count = verifications_collection.count_documents({"worker_uuid": worker_uuid})
        recent_verifications = list(verifications_collection.find(
            {"worker_uuid": worker_uuid}
        ).sort("time", -1).limit(10))
        
        # Remove _id fields
        for verification in recent_verifications:
            if "_id" in verification:
                del verification["_id"]
    
    return {
        "worker_uuid": worker_uuid,
        "worker_name": worker.get("name"),
        "total_verifications": total_count,
        "recent_verifications": recent_verifications
    }