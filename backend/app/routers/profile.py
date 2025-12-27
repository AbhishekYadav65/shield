from fastapi import APIRouter, HTTPException, status
from app.database import (
    get_users_collection, 
    get_workplace_bindings_collection,
    get_shifts_collection,
    get_verifications_collection,
    is_using_fallback
)
from app.fallback import (
    find_user_by_uuid,
    find_workplace_binding,
    get_shifts_by_worker,
    get_verifications_by_worker,
    get_verifications_by_customer
)
from typing import Dict, Any, List

router = APIRouter()

@router.get("/profile/{uuid}")
async def get_profile(uuid: str):
    """
    Get complete user profile.
    
    Used by: All roles
    
    Returns:
    - Basic profile (name, role, phone, created_at)
    - Role-specific data:
      - Worker: workplace bindings, shift history, verification count
      - Customer: verification history
      - Supervisor: managed workers count
      - Police: access level info
    """
    
    # Get user data
    if is_using_fallback():
        user = find_user_by_uuid(uuid)
    else:
        users_collection = get_users_collection()
        if users_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        user = users_collection.find_one({"uuid": uuid})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Remove MongoDB _id field if present
    if "_id" in user:
        del user["_id"]
    
    # Build base profile
    profile = {
        "uuid": user.get("uuid"),
        "role": user.get("role"),
        "name": user.get("name"),
        "phone": user.get("phone"),
        "platform_links": user.get("platform_links", []),
        "created_at": user.get("created_at")
    }
    
    # Add role-specific data
    if user.get("role") == "worker":
        profile["worker_data"] = await _get_worker_data(uuid)
    elif user.get("role") == "customer":
        profile["customer_data"] = await _get_customer_data(uuid)
    elif user.get("role") == "supervisor":
        profile["supervisor_data"] = await _get_supervisor_data(uuid)
    elif user.get("role") == "police":
        profile["police_data"] = {"access_level": "standard"}
    
    return profile

async def _get_worker_data(worker_uuid: str) -> Dict[str, Any]:
    """Get worker-specific data"""
    
    # Get workplace binding
    if is_using_fallback():
        binding = find_workplace_binding(worker_uuid)
    else:
        bindings_collection = get_workplace_bindings_collection()
        binding = bindings_collection.find_one({"uuid": worker_uuid, "active": True}) if bindings_collection else None
    
    workplace_info = None
    if binding:
        if "_id" in binding:
            del binding["_id"]
        workplace_info = {
            "workplace": binding.get("workplace"),
            "location": binding.get("location"),
            "supervisor_id": binding.get("supervisor_id"),
            "bound_at": binding.get("created_at")
        }
    
    # Get shift history
    if is_using_fallback():
        shifts = get_shifts_by_worker(worker_uuid)
    else:
        shifts_collection = get_shifts_collection()
        if shifts_collection:
            shifts = list(shifts_collection.find({"uuid": worker_uuid}).sort("start", -1).limit(10))
            # Remove _id fields
            for shift in shifts:
                if "_id" in shift:
                    del shift["_id"]
        else:
            shifts = []
    
    # Get verification count
    if is_using_fallback():
        verifications = get_verifications_by_worker(worker_uuid)
        verification_count = len(verifications)
    else:
        verifications_collection = get_verifications_collection()
        verification_count = verifications_collection.count_documents({"worker_uuid": worker_uuid}) if verifications_collection else 0
    
    return {
        "workplace_binding": workplace_info,
        "shift_history": shifts,
        "total_shifts": len(shifts),
        "verification_count": verification_count
    }

async def _get_customer_data(customer_uuid: str) -> Dict[str, Any]:
    """Get customer-specific data"""
    
    # Get verification history
    if is_using_fallback():
        verifications = get_verifications_by_customer(customer_uuid)
    else:
        verifications_collection = get_verifications_collection()
        if verifications_collection:
            verifications = list(verifications_collection.find({"customer_uuid": customer_uuid}).sort("time", -1).limit(20))
            # Remove _id fields
            for verification in verifications:
                if "_id" in verification:
                    del verification["_id"]
        else:
            verifications = []
    
    return {
        "verification_history": verifications,
        "total_verifications": len(verifications)
    }

async def _get_supervisor_data(supervisor_uuid: str) -> Dict[str, Any]:
    """Get supervisor-specific data"""
    
    # Count managed workers
    if is_using_fallback():
        from app.fallback import get_bindings_by_supervisor
        bindings = get_bindings_by_supervisor(supervisor_uuid)
        managed_workers_count = len(bindings)
    else:
        bindings_collection = get_workplace_bindings_collection()
        managed_workers_count = bindings_collection.count_documents({"supervisor_id": supervisor_uuid, "active": True}) if bindings_collection else 0
    
    # Get active shifts count
    if is_using_fallback():
        from app.fallback import _fallback_data
        active_shifts = [s for s in _fallback_data["shifts"] if s.get("supervisor_id") == supervisor_uuid and s.get("end") is None]
        active_shifts_count = len(active_shifts)
    else:
        shifts_collection = get_shifts_collection()
        active_shifts_count = shifts_collection.count_documents({"supervisor_id": supervisor_uuid, "end": None}) if shifts_collection else 0
    
    return {
        "managed_workers_count": managed_workers_count,
        "active_shifts_count": active_shifts_count
    }

@router.get("/profile/{uuid}/shifts")
async def get_user_shifts(uuid: str, limit: int = 20):
    """
    Get shift history for a worker.
    
    Used by: Worker dashboard
    
    Query params:
    - limit: number of shifts to return (default 20)
    """
    
    if is_using_fallback():
        shifts = get_shifts_by_worker(uuid)
        # Sort by start time (most recent first)
        shifts.sort(key=lambda x: x.get("start", ""), reverse=True)
        shifts = shifts[:limit]
    else:
        shifts_collection = get_shifts_collection()
        if shifts_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        shifts = list(shifts_collection.find({"uuid": uuid}).sort("start", -1).limit(limit))
        # Remove _id fields
        for shift in shifts:
            if "_id" in shift:
                del shift["_id"]
    
    return {
        "uuid": uuid,
        "shifts": shifts,
        "count": len(shifts)
    }