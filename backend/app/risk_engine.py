from datetime import datetime, time
from typing import Dict, Any
from app.models import RiskState

# Risk scoring configuration
RISK_THRESHOLDS = {
    "green": (0, 30),      # 0-30: Green (low risk)
    "yellow": (31, 60),    # 31-60: Yellow (medium risk)
    "red": (61, 100)       # 61-100: Red (high risk)
}

# Time-based risk zones (24-hour format)
HIGH_RISK_HOURS = [
    (22, 5),   # 10 PM to 5 AM (late night)
]

# Mock high-risk zones (in real system, would be from crime database)
HIGH_RISK_ZONES = [
    "zone_red_1",
    "zone_red_2",
    "isolated_area",
    "low_visibility_zone"
]

def calculate_risk_score(
    worker_data: Dict[str, Any],
    current_time: datetime = None,
    location_zone: str = None,
    complaint_count: int = 0
) -> int:
    """
    Calculate risk score for a worker (0-100).
    
    Higher score = Higher risk
    
    Factors:
    - Time of day (late night = higher risk)
    - Location zone (high-crime areas = higher risk)
    - Complaint history (more complaints = higher risk)
    - Account age (newer accounts = slightly higher risk)
    
    Args:
        worker_data: Worker profile dictionary
        current_time: Current datetime (defaults to now)
        location_zone: Zone identifier (optional)
        complaint_count: Number of complaints against worker
    
    Returns:
        Risk score (0-100)
    """
    if current_time is None:
        current_time = datetime.utcnow()
    
    risk_score = 0
    
    # Factor 1: Time of day (0-30 points)
    time_risk = _calculate_time_risk(current_time)
    risk_score += time_risk
    
    # Factor 2: Location zone (0-25 points)
    zone_risk = _calculate_zone_risk(location_zone)
    risk_score += zone_risk
    
    # Factor 3: Complaint history (0-30 points)
    complaint_risk = _calculate_complaint_risk(complaint_count)
    risk_score += complaint_risk
    
    # Factor 4: Account age (0-15 points)
    account_risk = _calculate_account_age_risk(worker_data)
    risk_score += account_risk
    
    # Cap at 100
    risk_score = min(risk_score, 100)
    
    return risk_score

def _calculate_time_risk(current_time: datetime) -> int:
    """
    Calculate risk based on time of day.
    Late night hours = higher risk.
    
    Returns: 0-30 points
    """
    current_hour = current_time.hour
    
    # Check if current time falls in high-risk hours
    for start_hour, end_hour in HIGH_RISK_HOURS:
        if start_hour > end_hour:  # Spans midnight (e.g., 22 to 5)
            if current_hour >= start_hour or current_hour < end_hour:
                return 30  # High risk time
        else:  # Normal range
            if start_hour <= current_hour < end_hour:
                return 30
    
    # Evening hours (6 PM - 10 PM) - medium risk
    if 18 <= current_hour < 22:
        return 15
    
    # Daytime hours - low risk
    return 0

def _calculate_zone_risk(location_zone: str) -> int:
    """
    Calculate risk based on location zone.
    High-crime areas = higher risk.
    
    Returns: 0-25 points
    """
    if location_zone is None:
        return 5  # Unknown location = slight risk
    
    # Check if zone is flagged as high-risk
    if location_zone in HIGH_RISK_ZONES:
        return 25
    
    # Check for specific zone patterns
    if "isolated" in location_zone.lower():
        return 20
    
    if "low_visibility" in location_zone.lower():
        return 15
    
    # Normal zone
    return 0

def _calculate_complaint_risk(complaint_count: int) -> int:
    """
    Calculate risk based on complaint history.
    More complaints = higher risk.
    
    Returns: 0-30 points
    """
    if complaint_count == 0:
        return 0
    elif complaint_count == 1:
        return 10
    elif complaint_count == 2:
        return 20
    else:  # 3+ complaints
        return 30

def _calculate_account_age_risk(worker_data: Dict[str, Any]) -> int:
    """
    Calculate risk based on account age.
    Very new accounts = slightly higher risk.
    
    Returns: 0-15 points
    """
    created_at = worker_data.get("created_at")
    
    if created_at is None:
        return 10  # Unknown = medium risk
    
    # Convert string to datetime if needed
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except:
            return 10
    
    account_age_days = (datetime.utcnow() - created_at).days
    
    if account_age_days < 7:  # Less than 1 week
        return 15
    elif account_age_days < 30:  # Less than 1 month
        return 10
    elif account_age_days < 90:  # Less than 3 months
        return 5
    else:  # 3+ months
        return 0

def get_risk_state(risk_score: int) -> RiskState:
    """
    Convert numeric risk score to risk state (Green/Yellow/Red).
    
    Args:
        risk_score: Risk score (0-100)
    
    Returns:
        RiskState enum (GREEN, YELLOW, or RED)
    """
    if RISK_THRESHOLDS["green"][0] <= risk_score <= RISK_THRESHOLDS["green"][1]:
        return RiskState.GREEN
    elif RISK_THRESHOLDS["yellow"][0] <= risk_score <= RISK_THRESHOLDS["yellow"][1]:
        return RiskState.YELLOW
    else:  # RED zone
        return RiskState.RED

def should_restrict_allocation(risk_state: RiskState, task_type: str = None) -> bool:
    """
    Determine if worker should be restricted from certain tasks.
    
    This is where allocation rules are enforced:
    - Red risk workers cannot serve vulnerable customers
    - Red risk workers cannot work in high-risk zones
    
    Args:
        risk_state: Worker's current risk state
        task_type: Type of task (e.g., "minor_customer", "female_late_night")
    
    Returns:
        True if allocation should be restricted, False otherwise
    """
    # Red risk = restrict from sensitive tasks
    if risk_state == RiskState.RED:
        if task_type in [
            "minor_customer",
            "female_late_night",
            "late_night_doorstep",
            "isolated_pickup",
            "high_crime_zone"
        ]:
            return True
    
    # Yellow risk = restrict from very sensitive tasks only
    if risk_state == RiskState.YELLOW:
        if task_type in ["minor_customer"]:
            return True
    
    # Green = no restrictions
    return False

def get_risk_details(risk_score: int) -> Dict[str, Any]:
    """
    Get detailed risk information for display.
    
    Returns dictionary with:
    - score: numeric score
    - state: green/yellow/red
    - message: human-readable explanation
    """
    risk_state = get_risk_state(risk_score)
    
    messages = {
        RiskState.GREEN: "Low risk - All allocations permitted",
        RiskState.YELLOW: "Medium risk - Some restrictions apply",
        RiskState.RED: "High risk - Significant restrictions apply"
    }
    
    return {
        "score": risk_score,
        "state": risk_state.value,
        "message": messages[risk_state]
    }