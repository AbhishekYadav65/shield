from fastapi import APIRouter, HTTPException, status
from app.models import WorkplaceBindRequest
from app.database import (
    get_users_collection,
    get_workplace_bindings_collection,
    is_using_fallback
)
from app.fallback import (
    find_user_by_uuid,
    insert_workplace_binding,
    find_workplace_binding
)
from datetime import datetime

router = APIRouter()

@router.post("/workplace/bind")
async def bind_worker_to_workplace(request: WorkplaceBindRequest):
    """
    Bind a worker to a workplace.
    
    Used by: Supervisors
    
    Process:
    1. Verify worker exists and is a worker role
    2. Verify supervisor exists and is a supervisor role
    3. Check if worker already has active binding
    4. Create workplace binding
    
    This is NOT done daily - only when worker joins workplace.
    Worker must be bound before they can start shifts.
    """
    
    # Validate required fields
    if not request.worker_uuid or not request.workplace or not request.supervisor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Worker UUID, workplace, and supervisor ID are required"
        )
    
    # Verify worker exists and is a worker
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
    
    # Verify supervisor exists and is a supervisor
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
    
    # Check if worker already has active binding
    if is_using_fallback():
        existing_binding = find_workplace_binding(request.worker_uuid)
    else:
        bindings_collection = get_workplace_bindings_collection()
        if bindings_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        existing_binding = bindings_collection.find_one({
            "uuid": request.worker_uuid,
            "active": True
        })
    
    if existing_binding:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Worker already bound to workplace: {existing_binding.get('workplace')}"
        )
    
    # Create binding
    binding_data = {
        "uuid": request.worker_uuid,
        "workplace": request.workplace,
        "location": request.location,
        "supervisor_id": request.supervisor_id,
        "active": True,
        "created_at": datetime.utcnow().isoformat()
    }
    
    try:
        if is_using_fallback():
            success = insert_workplace_binding(binding_data)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create workplace binding"
                )
        else:
            bindings_collection = get_workplace_bindings_collection()
            if bindings_collection is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database unavailable"
                )
            bindings_collection.insert_one(binding_data)
        
        return {
            "success": True,
            "message": f"Worker {worker.get('name')} bound to {request.workplace}",
            "binding": {
                "worker_uuid": request.worker_uuid,
                "worker_name": worker.get("name"),
                "workplace": request.workplace,
                "location": request.location,
                "supervisor_id": request.supervisor_id,
                "supervisor_name": supervisor.get("name"),
                "created_at": binding_data["created_at"]
            }
        }
    
    except Exception as e:
        print(f"Workplace binding error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create binding: {str(e)}"
        )

@router.get("/workplace/bindings/{supervisor_id}")
async def get_supervisor_bindings(supervisor_id: str):
    """
    Get all workplace bindings managed by a supervisor.
    
    Used by: Supervisor dashboard
    
    Returns list of workers bound to workplaces under this supervisor.
    """
    
    # Verify supervisor exists
    if is_using_fallback():
        supervisor = find_user_by_uuid(supervisor_id)
    else:
        users_collection = get_users_collection()
        if users_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        supervisor = users_collection.find_one({"uuid": supervisor_id})
    
    if not supervisor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supervisor not found"
        )
    
    # Get bindings
    if is_using_fallback():
        from app.fallback import get_bindings_by_supervisor
        bindings = get_bindings_by_supervisor(supervisor_id)
    else:
        bindings_collection = get_workplace_bindings_collection()
        if bindings_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        bindings = list(bindings_collection.find({"supervisor_id": supervisor_id, "active": True}))
        # Remove _id fields
        for binding in bindings:
            if "_id" in binding:
                del binding["_id"]
    
    # Enrich with worker names
    enriched_bindings = []
    for binding in bindings:
        worker_uuid = binding.get("uuid")
        
        if is_using_fallback():
            worker = find_user_by_uuid(worker_uuid)
        else:
            users_collection = get_users_collection()
            worker = users_collection.find_one({"uuid": worker_uuid}) if users_collection else None
        
        enriched_binding = {
            **binding,
            "worker_name": worker.get("name") if worker else "Unknown"
        }
        enriched_bindings.append(enriched_binding)
    
    return {
        "supervisor_id": supervisor_id,
        "supervisor_name": supervisor.get("name"),
        "bindings": enriched_bindings,
        "count": len(enriched_bindings)
    }

@router.get("/workplace/binding/{worker_uuid}")
async def get_worker_binding(worker_uuid: str):
    """
    Get active workplace binding for a worker.
    
    Used by: Worker dashboard, shift start validation
    
    Returns worker's current workplace binding or null if none.
    """
    
    if is_using_fallback():
        binding = find_workplace_binding(worker_uuid)
    else:
        bindings_collection = get_workplace_bindings_collection()
        if bindings_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        binding = bindings_collection.find_one({"uuid": worker_uuid, "active": True})
    
    if not binding:
        return {
            "worker_uuid": worker_uuid,
            "has_binding": False,
            "binding": None
        }
    
    # Remove _id field
    if "_id" in binding:
        del binding["_id"]
    
    return {
        "worker_uuid": worker_uuid,
        "has_binding": True,
        "binding": binding
    }