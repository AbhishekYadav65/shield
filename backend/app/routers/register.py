from fastapi import APIRouter, HTTPException, status
from app.models import RegisterRequest, RegisterResponse
from app.database import get_users_collection, is_using_fallback
from app.fallback import insert_user, find_user_by_phone
import uuid
import hashlib
from datetime import datetime

router = APIRouter()

def generate_uuid() -> str:
    """Generate unique user ID"""
    return str(uuid.uuid4())

def hash_data(data: str) -> str:
    """
    Create hash of sensitive data (face/ID images).
    In production, this would be proper biometric hashing.
    For MVP, we use SHA-256.
    """
    if not data:
        return ""
    return hashlib.sha256(data.encode()).hexdigest()

@router.post("/register", response_model=RegisterResponse)
async def register_user(request: RegisterRequest):
    """
    Universal user registration endpoint.
    
    Used by: workers, customers, supervisors, police
    
    Process:
    1. Validate phone number (check if already registered)
    2. Generate UUID
    3. Hash face and ID images (never store raw biometrics)
    4. Store user profile
    5. Return UUID and role
    
    Frontend should:
    - Store UUID in localStorage
    - Store role in localStorage
    - Redirect to appropriate dashboard
    """
    
    # Validate phone number is not empty
    if not request.phone or len(request.phone) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid phone number is required"
        )
    
    # Validate name
    if not request.name or len(request.name.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid name is required"
        )
    
    # Check if phone already registered
    if is_using_fallback():
        existing_user = find_user_by_phone(request.phone)
    else:
        users_collection = get_users_collection()
        if users_collection is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )
        existing_user = users_collection.find_one({"phone": request.phone})
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already registered"
        )
    
    # Generate UUID
    user_uuid = generate_uuid()
    
    # Hash face and ID images (never store raw biometrics)
    face_hash = hash_data(request.face_image) if request.face_image else ""
    id_hash = hash_data(request.id_image) if request.id_image else ""
    
    # Create user document
    user_data = {
        "uuid": user_uuid,
        "role": request.role.value,
        "name": request.name.strip(),
        "phone": request.phone,
        "face_hash": face_hash,
        "id_hash": id_hash,
        "platform_links": [request.platform_link] if request.platform_link else [],
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Store in database
    try:
        if is_using_fallback():
            success = insert_user(user_data)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to save user data"
                )
        else:
            users_collection = get_users_collection()
            if users_collection is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database unavailable"
                )
            users_collection.insert_one(user_data)
        
        # Return response
        return RegisterResponse(
            uuid=user_uuid,
            role=request.role.value,
            verification_status="pending",
            message=f"Registration successful as {request.role.value}"
        )
    
    except Exception as e:
        print(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.get("/register/check/{phone}")
async def check_phone_registered(phone: str):
    """
    Check if a phone number is already registered.
    Useful for frontend validation.
    
    Returns:
    - registered: boolean
    - role: user role if registered, null otherwise
    """
    try:
        if is_using_fallback():
            user = find_user_by_phone(phone)
        else:
            users_collection = get_users_collection()
            if users_collection is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database unavailable"
                )
            user = users_collection.find_one({"phone": phone})
        
        if user:
            return {
                "registered": True,
                "role": user.get("role"),
                "uuid": user.get("uuid")
            }
        else:
            return {
                "registered": False,
                "role": None,
                "uuid": None
            }
    
    except Exception as e:
        print(f"Phone check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Check failed: {str(e)}"
        )