from fastapi import APIRouter, Depends
from typing import Dict, List
import redis
from datetime import datetime, timedelta

from ..core.security import get_current_active_user
from ..core.config import settings
from ..services.security import SecurityService

router = APIRouter()

@router.get("/status")
async def get_security_status(
    security_service: SecurityService = Depends(SecurityService),
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Get the current security status including metrics, AI security events,
    and active defenses.
    """
    try:
        # Get security metrics
        metrics = await security_service.get_metrics()
        
        # Get AI security events
        ai_security = await security_service.get_ai_security_status()
        
        # Get active defenses
        active_defenses = await security_service.get_active_defenses()
        
        # Calculate overall threat level
        threat_level = await security_service.calculate_threat_level(
            metrics, ai_security
        )
        
        # Get blacklisted IPs count
        blacklisted_ips = await security_service.get_blacklisted_ips_count()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics,
            "ai_security": ai_security,
            "blacklisted_ips": blacklisted_ips,
            "threat_level": threat_level,
            "active_defenses": active_defenses
        }
        
    except Exception as e:
        # Log the error but don't expose internal details
        print(f"Error in security status endpoint: {str(e)}")
        return {
            "error": "Failed to retrieve security status",
            "status": "error"
        }
