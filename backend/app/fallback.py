import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

# Path to local JSON file
FALLBACK_FILE = os.path.join(os.path.dirname(__file__), "data", "local_fallback.json")

# In-memory cache
_fallback_data = {
    "users": [],
    "workplace_bindings": [],
    "shifts": [],
    "verifications": []
}

def _ensure_data_directory():
    """Create data directory if it doesn't exist"""
    data_dir = os.path.dirname(FALLBACK_FILE)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"✓ Created data directory: {data_dir}")

def _load_fallback_data():
    """Load data from JSON file into memory"""
    global _fallback_data
    
    _ensure_data_directory()
    
    if os.path.exists(FALLBACK_FILE):
        try:
            with open(FALLBACK_FILE, 'r') as f:
                _fallback_data = json.load(f)
            print(f"✓ Loaded fallback data from: {FALLBACK_FILE}")
        except Exception as e:
            print(f"⚠ Could not load fallback data: {str(e)}")
            _fallback_data = {
                "users": [],
                "workplace_bindings": [],
                "shifts": [],
                "verifications": []
            }
    else:
        print("⚠ No existing fallback file, starting fresh")

def _save_fallback_data():
    """Save in-memory data to JSON file"""
    global _fallback_data
    
    try:
        _ensure_data_directory()
        
        # Convert datetime objects to strings for JSON serialization
        serializable_data = _convert_for_json(_fallback_data)
        
        with open(FALLBACK_FILE, 'w') as f:
            json.dump(serializable_data, f, indent=2)
        
        return True
    except Exception as e:
        print(f"⚠ Could not save fallback data: {str(e)}")
        return False

def _convert_for_json(data):
    """Convert datetime objects to ISO format strings"""
    if isinstance(data, dict):
        return {k: _convert_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_convert_for_json(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data

def initialize_fallback():
    """Initialize fallback system - call this at startup"""
    _load_fallback_data()
    print("✓ Fallback system initialized")

# CRUD Operations for Users
def insert_user(user_data: Dict[str, Any]) -> bool:
    """Insert a new user"""
    _fallback_data["users"].append(user_data)
    return _save_fallback_data()

def find_user_by_uuid(uuid: str) -> Optional[Dict[str, Any]]:
    """Find user by UUID"""
    for user in _fallback_data["users"]:
        if user.get("uuid") == uuid:
            return user
    return None

def find_user_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    """Find user by phone number"""
    for user in _fallback_data["users"]:
        if user.get("phone") == phone:
            return user
    return None

def get_all_users() -> List[Dict[str, Any]]:
    """Get all users"""
    return _fallback_data["users"]

# CRUD Operations for Workplace Bindings
def insert_workplace_binding(binding_data: Dict[str, Any]) -> bool:
    """Insert a new workplace binding"""
    _fallback_data["workplace_bindings"].append(binding_data)
    return _save_fallback_data()

def find_workplace_binding(worker_uuid: str) -> Optional[Dict[str, Any]]:
    """Find active workplace binding for a worker"""
    for binding in _fallback_data["workplace_bindings"]:
        if binding.get("uuid") == worker_uuid and binding.get("active"):
            return binding
    return None

def get_bindings_by_supervisor(supervisor_id: str) -> List[Dict[str, Any]]:
    """Get all bindings managed by a supervisor"""
    return [b for b in _fallback_data["workplace_bindings"] 
            if b.get("supervisor_id") == supervisor_id]

# CRUD Operations for Shifts
def insert_shift(shift_data: Dict[str, Any]) -> bool:
    """Insert a new shift"""
    _fallback_data["shifts"].append(shift_data)
    return _save_fallback_data()

def find_shift_by_id(shift_id: str) -> Optional[Dict[str, Any]]:
    """Find shift by shift_id"""
    for shift in _fallback_data["shifts"]:
        if shift.get("shift_id") == shift_id:
            return shift
    return None

def find_shift_by_stt(stt: str) -> Optional[Dict[str, Any]]:
    """Find shift by STT (QR code data)"""
    for shift in _fallback_data["shifts"]:
        if shift.get("stt") == stt:
            return shift
    return None

def find_active_shift(worker_uuid: str) -> Optional[Dict[str, Any]]:
    """Find active shift for a worker (where end is None)"""
    for shift in _fallback_data["shifts"]:
        if shift.get("uuid") == worker_uuid and shift.get("end") is None:
            return shift
    return None

def update_shift(shift_id: str, update_data: Dict[str, Any]) -> bool:
    """Update a shift"""
    for i, shift in enumerate(_fallback_data["shifts"]):
        if shift.get("shift_id") == shift_id:
            _fallback_data["shifts"][i].update(update_data)
            return _save_fallback_data()
    return False

def get_shifts_by_worker(worker_uuid: str) -> List[Dict[str, Any]]:
    """Get all shifts for a worker"""
    return [s for s in _fallback_data["shifts"] if s.get("uuid") == worker_uuid]

# CRUD Operations for Verifications
def insert_verification(verification_data: Dict[str, Any]) -> bool:
    """Insert a new verification log"""
    _fallback_data["verifications"].append(verification_data)
    return _save_fallback_data()

def get_verifications_by_worker(worker_uuid: str) -> List[Dict[str, Any]]:
    """Get all verifications for a worker"""
    return [v for v in _fallback_data["verifications"] 
            if v.get("worker_uuid") == worker_uuid]

def get_verifications_by_customer(customer_uuid: str) -> List[Dict[str, Any]]:
    """Get all verifications by a customer"""
    return [v for v in _fallback_data["verifications"] 
            if v.get("customer_uuid") == customer_uuid]

def get_recent_verifications(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent verifications (for police dashboard)"""
    sorted_verifications = sorted(
        _fallback_data["verifications"],
        key=lambda x: x.get("time", ""),
        reverse=True
    )
    return sorted_verifications[:limit]