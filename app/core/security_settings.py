from typing import Dict, List
from pydantic_settings import BaseSettings

class SecuritySettings(BaseSettings):
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_SECURITY_DB: int = 1
    
    # JWT Settings
    JWT_SECRET_KEY: str = "your-secret-key"  # Change in production
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Rate Limiting
    RATE_LIMIT_DEFAULT: int = 100
    RATE_LIMIT_AI_ENDPOINTS: int = 50
    RATE_LIMIT_SECURITY: int = 20
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Security Headers
    TRUSTED_DOMAINS: List[str] = ["trusted-cdn.com", "api.huggingface.co"]
    CSP_REPORT_URI: str = "/api/security/csp-report"
    
    # AI Security
    AI_SECURITY_ENABLED: bool = True
    AI_THREAT_DETECTION_LEVEL: str = "strict"
    PROMPT_VALIDATION_ENABLED: bool = True
    MODEL_ACCESS_CONTROL_ENABLED: bool = True
    
    # Auto-Defense Settings
    AUTO_DEFENSE_ENABLED: bool = True
    AUTO_DEFENSE_THRESHOLDS: Dict[str, int] = {
        "rate_limit_violations": 10,
        "threat_detections": 5,
        "prompt_injection_attempts": 3,
        "model_abuse_attempts": 3
    }
    
    # Monitoring and Metrics
    SECURITY_METRICS_ENABLED: bool = True
    METRICS_RETENTION_DAYS: int = 30
    EVENT_LOG_MAX_SIZE: int = 1000
    METRICS_COLLECTION_INTERVAL: int = 60
    
    # Authentication
    API_KEY_REQUIRED: bool = True
    JWT_TOKEN_REQUIRED: bool = True
    MFA_ENABLED: bool = True
    MFA_ISSUER: str = "PinnacleCopilot"
    
    # Logging
    SECURITY_LOG_DIR: str = "logs/security"
    MAX_LOG_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # Alert Settings
    ALERT_SEVERITY_LEVELS: Dict[str, Dict[str, int]] = {
        "critical": {
            "rate_limit_violations": 10,
            "threat_detections": 5,
            "ai_security_events": 3
        },
        "high": {
            "rate_limit_violations": 5,
            "threat_detections": 3,
            "ai_security_events": 2
        },
        "medium": {
            "rate_limit_violations": 3,
            "threat_detections": 2,
            "ai_security_events": 1
        }
    }
    
    # AI Model Protection
    MODEL_PROTECTION_RULES: Dict[str, Dict] = {
        "max_tokens": 2000,
        "max_requests_per_minute": 50,
        "require_auth": True,
        "allowed_models": ["gpt-3.5-turbo", "gpt-4"],
        "blocked_content": [
            "malicious_code",
            "sensitive_data",
            "prohibited_content"
        ]
    }
    
    # Security Scopes
    SECURITY_SCOPES: Dict[str, str] = {
        "admin": "Full administrative access",
        "security": "Security management access",
        "ai_access": "AI model access",
        "metrics": "Security metrics access"
    }
    
    # Rate Limiting
    RATE_LIMIT_DEFAULT: int = 100
    RATE_LIMIT_AI_ENDPOINTS: int = 50
    RATE_LIMIT_SECURITY: int = 20
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Security Headers
    TRUSTED_DOMAINS: List[str] = ["trusted-cdn.com", "api.huggingface.co"]
    CSP_REPORT_URI: str = "/api/security/csp-report"
    
    # AI Security
    AI_SECURITY_ENABLED: bool = True
    AI_THREAT_DETECTION_LEVEL: str = "strict"  # strict, moderate, or basic
    PROMPT_VALIDATION_ENABLED: bool = True
    MODEL_ACCESS_CONTROL_ENABLED: bool = True
    
    # Auto-Defense Settings
    AUTO_DEFENSE_ENABLED: bool = True
    AUTO_DEFENSE_THRESHOLDS: Dict[str, int] = {
        "rate_limit_violations": 10,
        "threat_detections": 5,
        "prompt_injection_attempts": 3
    }
    
    # Monitoring and Metrics
    SECURITY_METRICS_ENABLED: bool = True
    METRICS_RETENTION_DAYS: int = 30
    EVENT_LOG_MAX_SIZE: int = 1000
    
    # Authentication
    API_KEY_REQUIRED: bool = True
    JWT_TOKEN_REQUIRED: bool = True
    
    class Config:
        env_prefix = "SECURITY_"

security_settings = SecuritySettings()
