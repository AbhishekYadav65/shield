from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enums for fixed choices
class UserRole(str, Enum):
    WORKER = "worker"
    CUSTOMER = "customer"
    SUPERVISOR = "supervisor"
    POLICE = "police"

class RiskState(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"

# Registration Request
class RegisterRequest(BaseModel):
    role: UserRole
    name: str
    phone: str
    face_image: Optional[str] = None  # base64 or hash
    id_image: Optional[str] = None    # base64 or hash
    platform_link: Optional[str] = None

# Registration Response
class RegisterResponse(BaseModel):
    uuid: str
    role: str
    verification_status: str
    message: str

# User Profile (Database Model)
class UserProfile(BaseModel):
    uuid: str
    role: str
    name: str
    phone: str
    face_hash: str
    id_hash: str
    platform_links: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Workplace Binding Request
class WorkplaceBindRequest(BaseModel):
    worker_uuid: str
    workplace: str
    location: str
    supervisor_id: str

# Workplace Binding (Database Model)
class WorkplaceBinding(BaseModel):
    uuid: str
    workplace: str
    supervisor_id: str
    location: str
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Shift Start Request
class ShiftStartRequest(BaseModel):
    worker_uuid: str
    supervisor_id: str
    workplace: str

# Shift End Request
class ShiftEndRequest(BaseModel):
    shift_id: str
    supervisor_id: str

# Shift (Database Model)
class Shift(BaseModel):
    shift_id: str
    uuid: str  # worker uuid
    start: datetime
    end: Optional[datetime] = None
    stt: str  # Shift Trust Token (QR code data)
    risk_state: RiskState = RiskState.GREEN
    workplace: str
    supervisor_id: str

# Shift Status Response
class ShiftStatusResponse(BaseModel):
    active: bool
    shift_id: Optional[str] = None
    stt: Optional[str] = None
    risk_state: Optional[str] = None
    start_time: Optional[datetime] = None
    workplace: Optional[str] = None

# Worker Verification Request
class VerifyWorkerRequest(BaseModel):
    stt: str  # scanned QR code data
    customer_uuid: str

# Worker Verification Response
class VerifyWorkerResponse(BaseModel):
    verified: bool
    worker_name: Optional[str] = None
    worker_photo: Optional[str] = None
    employer: Optional[str] = None
    shift_active: bool = False
    risk_color: Optional[str] = None
    message: str

# Verification Log (Database Model)
class Verification(BaseModel):
    worker_uuid: str
    customer_uuid: str
    time: datetime = Field(default_factory=datetime.utcnow)
    location: Optional[str] = None

# Police Scan Request
class PoliceScanRequest(BaseModel):
    stt: str  # scanned QR code data
    officer_uuid: str

# Police Scan Response
class PoliceScanResponse(BaseModel):
    verified: bool
    identity: Optional[dict] = None
    workplace: Optional[dict] = None
    shift_status: Optional[dict] = None
    risk_state: Optional[str] = None
    supervisor_name: Optional[str] = None
    message: str