from datetime import datetime, timedelta
from typing import Optional, Dict, List
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError
import pyotp
import redis
from ..core.security_settings import security_settings
from ..core.security_audit import security_audit_logger

# Initialize Redis for session storage
redis_client = redis.Redis(
    host=security_settings.REDIS_HOST,
    port=security_settings.REDIS_PORT,
    db=security_settings.REDIS_SECURITY_DB,
    decode_responses=True
)

# Security configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes=security_settings.SECURITY_SCOPES
)

class Token(BaseModel):
    access_token: str
    token_type: str
    mfa_required: bool = False
    mfa_token: Optional[str] = None

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []
    mfa_verified: bool = False

class MFASetup(BaseModel):
    secret: str
    uri: str

class MFAValidation(BaseModel):
    token: str

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def create_access_token(
    data: dict,
    scopes: List[str] = [],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT token with scopes"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({
        "exp": expire,
        "scopes": scopes
    })
    
    # Log token creation
    security_audit_logger.log_audit_event(
        user=data.get("sub", "unknown"),
        action="token_creation",
        resource="access_token",
        status="success",
        details={"scopes": scopes}
    )
    
    return jwt.encode(
        to_encode,
        security_settings.JWT_SECRET_KEY,
        algorithm=security_settings.JWT_ALGORITHM
    )

async def setup_mfa(username: str) -> MFASetup:
    """Set up MFA for a user"""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(
        username,
        issuer_name=security_settings.MFA_ISSUER
    )
    
    # Store the secret temporarily
    redis_client.setex(
        f"mfa_setup:{username}",
        300,  # Expires in 5 minutes
        secret
    )
    
    # Log MFA setup
    security_audit_logger.log_audit_event(
        user=username,
        action="mfa_setup",
        resource="mfa",
        status="initiated",
        details={}
    )
    
    return MFASetup(secret=secret, uri=uri)

async def verify_mfa(username: str, token: str) -> bool:
    """Verify MFA token"""
    secret = redis_client.get(f"mfa:{username}")
    if not secret:
        return False
    
    totp = pyotp.TOTP(secret)
    is_valid = totp.verify(token)
    
    # Log MFA verification attempt
    security_audit_logger.log_audit_event(
        user=username,
        action="mfa_verification",
        resource="mfa",
        status="success" if is_valid else "failed",
        details={}
    )
    
    return is_valid

async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme)
) -> TokenData:
    """Get current user from JWT token with scope verification"""
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    
    try:
        # Decode JWT
        payload = jwt.decode(
            token,
            security_settings.JWT_SECRET_KEY,
            algorithms=[security_settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
        token_scopes = payload.get("scopes", [])
        mfa_verified = payload.get("mfa_verified", False)
        token_data = TokenData(
            username=username,
            scopes=token_scopes,
            mfa_verified=mfa_verified
        )
    except (JWTError, ValidationError) as e:
        # Log authentication failure
        security_audit_logger.log_audit_event(
            user="unknown",
            action="token_validation",
            resource="access_token",
            status="failed",
            details={"error": str(e)}
        )
        raise credentials_exception
    
    # Verify required scopes
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            # Log insufficient permissions
            security_audit_logger.log_audit_event(
                user=username,
                action="scope_verification",
                resource=scope,
                status="failed",
                details={"required_scope": scope}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    
    # Verify MFA if required
    if security_settings.MFA_ENABLED and not token_data.mfa_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MFA verification required",
            headers={"X-MFA-Required": "true"}
        )
    
    # Log successful authentication
    security_audit_logger.log_audit_event(
        user=username,
        action="authentication",
        resource="access_token",
        status="success",
        details={"scopes": token_data.scopes}
    )
    
    return token_data

async def validate_api_key(api_key: str = Security(OAuth2PasswordBearer)) -> bool:
    """Validate API key"""
    # Add your API key validation logic here
    try:
        # Example: Check against Redis or database
        is_valid = await redis_client.sismember("valid_api_keys", api_key)
        
        # Log API key validation
        security_audit_logger.log_audit_event(
            user="api_client",
            action="api_key_validation",
            resource="api_key",
            status="success" if is_valid else "failed",
            details={}
        )
        
        return is_valid
    except Exception as e:
        # Log validation error
        security_audit_logger.log_audit_event(
            user="api_client",
            action="api_key_validation",
            resource="api_key",
            status="error",
            details={"error": str(e)}
        )
        return False
