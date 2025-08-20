from fastapi import APIRouter, Depends, HTTPException, Security
from typing import Dict, List
from datetime import datetime
from ..core.security import get_current_user
from ..core.advanced_security import advanced_security
from ..core.ai_security import ai_security_manager
from ..core.security_monitor import security_monitor

router = APIRouter(prefix="/api/security", tags=["security"])

@router.get("/dashboard")
async def get_security_dashboard(
    current_user: Dict = Security(get_current_user, scopes=["admin"])
):
    """Get comprehensive security dashboard data"""
    try:
        # Get security status from different components
        monitor_status = await security_monitor.get_security_status()
        advanced_status = await advanced_security.get_security_status()
        ai_status = await ai_security_manager.get_ai_security_status()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "threat_level": monitor_status["threat_level"],
            "threat_level_text": monitor_status["threat_level_text"],
            "alerts": {
                "recent": monitor_status["recent_alerts"],
                "count": {
                    "critical": len([a for a in monitor_status["recent_alerts"] 
                                   if a["severity"] == "critical"]),
                    "high": len([a for a in monitor_status["recent_alerts"] 
                               if a["severity"] == "high"]),
                    "medium": len([a for a in monitor_status["recent_alerts"] 
                                 if a["severity"] == "medium"]),
                    "low": len([a for a in monitor_status["recent_alerts"] 
                              if a["severity"] == "low"])
                }
            },
            "metrics": {
                "general": monitor_status["metrics"],
                "ai_specific": ai_status["metrics"]
            },
            "events": {
                "recent": monitor_status["recent_events"],
                "ai_events": ai_status["events"]
            },
            "defenses": {
                "active": advanced_status["active_defenses"],
                "blocked_requests": advanced_status["blocked_requests"]
            },
            "ai_security": {
                "model_usage": ai_status["model_usage"],
                "recent_threats": [
                    event for event in ai_status["events"]
                    if "threat" in event.lower()
                ]
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving security dashboard data: {str(e)}"
        )

@router.get("/alerts")
async def get_security_alerts(
    current_user: Dict = Security(get_current_user, scopes=["admin"])
):
    """Get detailed security alerts"""
    return {
        "alerts": await security_monitor.get_recent_alerts(limit=50)
    }

@router.get("/threats")
async def get_active_threats(
    current_user: Dict = Security(get_current_user, scopes=["admin"])
):
    """Get active security threats"""
    monitor_status = await security_monitor.get_security_status()
    advanced_status = await advanced_security.get_security_status()
    
    return {
        "active_threats": [
            event for event in monitor_status["recent_events"]
            if event["type"] == "threat_detected"
        ],
        "blocked_ips": advanced_status.get("blocked_ips", []),
        "threat_patterns": await advanced_security.get_threat_patterns()
    }

@router.get("/ai-security")
async def get_ai_security_status(
    current_user: Dict = Security(get_current_user, scopes=["admin"])
):
    """Get AI security specific status"""
    return await ai_security_manager.get_ai_security_status()

@router.post("/update-defense-rules")
async def update_defense_rules(
    rules: Dict,
    current_user: Dict = Security(get_current_user, scopes=["admin"])
):
    """Update security defense rules"""
    try:
        await advanced_security.update_defense_rules(rules)
        return {"message": "Defense rules updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating defense rules: {str(e)}"
        )
