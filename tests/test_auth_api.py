import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException, status, Security
from datetime import datetime, timedelta
import jwt
import pyotp
import json

from app.main import app
from app.core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    setup_mfa,
    verify_mfa,
    get_current_user,
    validate_api_key,
    Token,
    TokenData,
    MFASetup,
    MFAValidation
)
from app.core.security_settings import security_settings

# Mock user data
mock_user_data = {
    "id": "test_user_id",
    "email": "test@example.com",
    "username": "testuser",
    "hashed_password": "$2b$12$testhashedpassword",
    "is_active": True,
    "scopes": ["read", "write"]
}

@pytest.fixture
def client():
    """Create test client"""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    with patch('app.core.auth.redis_client') as mock_redis:
        mock_redis.get = Mock()
        mock_redis.setex = Mock()
        mock_redis.sismember = AsyncMock(return_value=True)
        yield mock_redis

@pytest.fixture
def mock_security_audit_logger():
    """Mock security audit logger"""
    with patch('app.core.auth.security_audit_logger') as mock_logger:
        mock_logger.log_audit_event = Mock()
        yield mock_logger

class TestPasswordFunctions:
    """Test password-related functions"""

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        plain_password = "test_password"
        hashed_password = get_password_hash(plain_password)

        assert verify_password(plain_password, hashed_password) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        plain_password = "test_password"
        wrong_password = "wrong_password"
        hashed_password = get_password_hash(plain_password)

        assert verify_password(wrong_password, hashed_password) is False

    def test_get_password_hash(self):
        """Test password hashing"""
        password = "test_password"
        hashed = get_password_hash(password)

        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50

    def test_verify_password_with_empty_strings(self):
        """Test password verification with empty strings"""
        assert verify_password("", "") is False
        assert verify_password("password", "") is False
        assert verify_password("", "hashed") is False

class TestTokenFunctions:
    """Test token-related functions"""

    def test_create_access_token_basic(self, mock_security_audit_logger):
        """Test basic access token creation"""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token can be decoded
        decoded = jwt.decode(
            token,
            security_settings.JWT_SECRET_KEY,
            algorithms=[security_settings.JWT_ALGORITHM]
        )
        assert decoded["sub"] == "testuser"
        assert "exp" in decoded

    def test_create_access_token_with_scopes(self, mock_security_audit_logger):
        """Test access token creation with scopes"""
        data = {"sub": "testuser"}
        scopes = ["read", "write"]
        token = create_access_token(data, scopes)

        decoded = jwt.decode(
            token,
            security_settings.JWT_SECRET_KEY,
            algorithms=[security_settings.JWT_ALGORITHM]
        )
        assert decoded["scopes"] == scopes

    def test_create_access_token_with_expiration(self, mock_security_audit_logger):
        """Test access token creation with custom expiration"""
        data = {"sub": "testuser"}
        expires_delta = timedelta(hours=1)
        token = create_access_token(data, expires_delta=expires_delta)

        decoded = jwt.decode(
            token,
            security_settings.JWT_SECRET_KEY,
            algorithms=[security_settings.JWT_ALGORITHM]
        )

        # Verify expiration is set correctly
        exp_time = datetime.fromtimestamp(decoded["exp"])
        assert exp_time > datetime.utcnow()

    def test_create_access_token_logging(self, mock_security_audit_logger):
        """Test that token creation is logged"""
        data = {"sub": "testuser"}
        scopes = ["read"]

        create_access_token(data, scopes)

        mock_security_audit_logger.log_audit_event.assert_called_once_with(
            user="testuser",
            action="token_creation",
            resource="access_token",
            status="success",
            details={"scopes": scopes}
        )

class TestMFAFunctions:
    """Test MFA-related functions"""

    @pytest.mark.asyncio
    async def test_setup_mfa_success(self, mock_redis_client, mock_security_audit_logger):
        """Test successful MFA setup"""
        username = "testuser"

        result = await setup_mfa(username)

        assert isinstance(result, MFASetup)
        assert result.secret is not None
        assert result.uri is not None
        assert len(result.secret) == 32  # Base32 length

        # Verify Redis storage
        mock_redis_client.setex.assert_called_once()
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][0] == f"mfa_setup:{username}"
        assert call_args[0][1] == 300  # 5 minutes
        assert call_args[0][2] == result.secret

    @pytest.mark.asyncio
    async def test_setup_mfa_logging(self, mock_redis_client, mock_security_audit_logger):
        """Test that MFA setup is logged"""
        username = "testuser"

        await setup_mfa(username)

        mock_security_audit_logger.log_audit_event.assert_called_once_with(
            user=username,
            action="mfa_setup",
            resource="mfa",
            status="initiated",
            details={}
        )

    @pytest.mark.asyncio
    async def test_verify_mfa_success(self, mock_redis_client, mock_security_audit_logger):
        """Test successful MFA verification"""
        username = "testuser"
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        valid_token = totp.now()

        # Mock Redis to return the secret
        mock_redis_client.get.return_value = secret

        result = await verify_mfa(username, valid_token)

        assert result is True
        mock_redis_client.get.assert_called_once_with(f"mfa:{username}")

    @pytest.mark.asyncio
    async def test_verify_mfa_no_secret(self, mock_redis_client, mock_security_audit_logger):
        """Test MFA verification when no secret exists"""
        username = "testuser"
        token = "123456"

        # Mock Redis to return None
        mock_redis_client.get.return_value = None

        result = await verify_mfa(username, token)

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_mfa_invalid_token(self, mock_redis_client, mock_security_audit_logger):
        """Test MFA verification with invalid token"""
        username = "testuser"
        secret = pyotp.random_base32()
        invalid_token = "000000"

        # Mock Redis to return the secret
        mock_redis_client.get.return_value = secret

        result = await verify_mfa(username, invalid_token)

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_mfa_logging(self, mock_redis_client, mock_security_audit_logger):
        """Test that MFA verification is logged"""
        username = "testuser"
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        valid_token = totp.now()

        mock_redis_client.get.return_value = secret

        await verify_mfa(username, valid_token)

        mock_security_audit_logger.log_audit_event.assert_called_once_with(
            user=username,
            action="mfa_verification",
            resource="mfa",
            status="success",
            details={}
        )

class TestGetCurrentUser:
    """Test get_current_user function"""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, mock_security_audit_logger):
        """Test getting current user with valid token"""
        # Create a valid token
        token_data = {
            "sub": "testuser",
            "scopes": ["read", "write"],
            "mfa_verified": True,
            "exp": datetime.utcnow() + timedelta(minutes=15)
        }
        token = jwt.encode(
            token_data,
            security_settings.JWT_SECRET_KEY,
            algorithm=security_settings.JWT_ALGORITHM
        )

        # Mock security scopes
        security_scopes = Mock()
        security_scopes.scopes = ["read"]
        security_scopes.scope_str = "read"

        result = await get_current_user(security_scopes, token)

        assert isinstance(result, TokenData)
        assert result.username == "testuser"
        assert result.scopes == ["read", "write"]
        assert result.mfa_verified is True

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_security_audit_logger):
        """Test getting current user with invalid token"""
        invalid_token = "invalid.token.here"
        security_scopes = Mock()
        security_scopes.scopes = ["read"]
        security_scopes.scope_str = "read"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(security_scopes, invalid_token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_missing_username(self, mock_security_audit_logger):
        """Test getting current user with token missing username"""
        token_data = {
            "scopes": ["read"],
            "exp": datetime.utcnow() + timedelta(minutes=15)
        }
        token = jwt.encode(
            token_data,
            security_settings.JWT_SECRET_KEY,
            algorithm=security_settings.JWT_ALGORITHM
        )

        security_scopes = Mock()
        security_scopes.scopes = ["read"]
        security_scopes.scope_str = "read"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(security_scopes, token)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_insufficient_scopes(self, mock_security_audit_logger):
        """Test getting current user with insufficient scopes"""
        token_data = {
            "sub": "testuser",
            "scopes": ["read"],  # Only read scope
            "exp": datetime.utcnow() + timedelta(minutes=15)
        }
        token = jwt.encode(
            token_data,
            security_settings.JWT_SECRET_KEY,
            algorithm=security_settings.JWT_ALGORITHM
        )

        security_scopes = Mock()
        security_scopes.scopes = ["read", "write"]  # Requires write scope
        security_scopes.scope_str = "read write"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(security_scopes, token)

        assert exc_info.value.status_code == 403
        assert "Not enough permissions" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_mfa_required(self, mock_security_audit_logger):
        """Test getting current user when MFA is required but not verified"""
        # Mock MFA enabled
        with patch.object(security_settings, 'MFA_ENABLED', True):
            token_data = {
                "sub": "testuser",
                "scopes": ["read"],
                "mfa_verified": False,  # MFA not verified
                "exp": datetime.utcnow() + timedelta(minutes=15)
            }
            token = jwt.encode(
                token_data,
                security_settings.JWT_SECRET_KEY,
                algorithm=security_settings.JWT_ALGORITHM
            )

            security_scopes = Mock()
            security_scopes.scopes = ["read"]
            security_scopes.scope_str = "read"

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(security_scopes, token)

            assert exc_info.value.status_code == 401
            assert "MFA verification required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_logging_success(self, mock_security_audit_logger):
        """Test that successful authentication is logged"""
        token_data = {
            "sub": "testuser",
            "scopes": ["read"],
            "mfa_verified": True,
            "exp": datetime.utcnow() + timedelta(minutes=15)
        }
        token = jwt.encode(
            token_data,
            security_settings.JWT_SECRET_KEY,
            algorithm=security_settings.JWT_ALGORITHM
        )

        security_scopes = Mock()
        security_scopes.scopes = ["read"]
        security_scopes.scope_str = "read"

        await get_current_user(security_scopes, token)

        mock_security_audit_logger.log_audit_event.assert_called_once_with(
            user="testuser",
            action="authentication",
            resource="access_token",
            status="success",
            details={"scopes": ["read"]}
        )

class TestValidateApiKey:
    """Test API key validation function"""

    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, mock_redis_client, mock_security_audit_logger):
        """Test successful API key validation"""
        api_key = "test_api_key_123"

        result = await validate_api_key(api_key)

        assert result is True
        mock_redis_client.sismember.assert_called_once_with("valid_api_keys", api_key)

    @pytest.mark.asyncio
    async def test_validate_api_key_failure(self, mock_redis_client, mock_security_audit_logger):
        """Test failed API key validation"""
        api_key = "invalid_api_key"

        # Mock Redis to return False
        mock_redis_client.sismember = AsyncMock(return_value=False)

        result = await validate_api_key(api_key)

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_api_key_exception(self, mock_redis_client, mock_security_audit_logger):
        """Test API key validation with exception"""
        api_key = "test_api_key"

        # Mock Redis to raise exception
        mock_redis_client.sismember = AsyncMock(side_effect=Exception("Redis error"))

        result = await validate_api_key(api_key)

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_api_key_logging_success(self, mock_redis_client, mock_security_audit_logger):
        """Test that successful API key validation is logged"""
        api_key = "test_api_key_123"

        await validate_api_key(api_key)

        mock_security_audit_logger.log_audit_event.assert_called_once_with(
            user="api_client",
            action="api_key_validation",
            resource="api_key",
            status="success",
            details={}
        )

    @pytest.mark.asyncio
    async def test_validate_api_key_logging_failure(self, mock_redis_client, mock_security_audit_logger):
        """Test that failed API key validation is logged"""
        api_key = "invalid_api_key"

        # Mock Redis to return False
        mock_redis_client.sismember = AsyncMock(return_value=False)

        await validate_api_key(api_key)

        mock_security_audit_logger.log_audit_event.assert_called_once_with(
            user="api_client",
            action="api_key_validation",
            resource="api_key",
            status="failed",
            details={}
        )

class TestAuthIntegration:
    """Integration tests for authentication system"""

    def test_token_data_model_validation(self):
        """Test TokenData model validation"""
        # Valid data
        token_data = TokenData(username="testuser", scopes=["read"], mfa_verified=True)
        assert token_data.username == "testuser"
        assert token_data.scopes == ["read"]
        assert token_data.mfa_verified is True

        # Default values
        token_data = TokenData()
        assert token_data.username is None
        assert token_data.scopes == []
        assert token_data.mfa_verified is False

    def test_token_model_validation(self):
        """Test Token model validation"""
        # Valid data
        token = Token(
            access_token="test_token",
            token_type="bearer",
            mfa_required=False,
            mfa_token=None
        )
        assert token.access_token == "test_token"
        assert token.token_type == "bearer"
        assert token.mfa_required is False
        assert token.mfa_token is None

        # With MFA
        token = Token(
            access_token="test_token",
            token_type="bearer",
            mfa_required=True,
            mfa_token="123456"
        )
        assert token.mfa_required is True
        assert token.mfa_token == "123456"

    def test_mfa_setup_model_validation(self):
        """Test MFASetup model validation"""
        mfa_setup = MFASetup(secret="test_secret", uri="test_uri")
        assert mfa_setup.secret == "test_secret"
        assert mfa_setup.uri == "test_uri"

    def test_mfa_validation_model_validation(self):
        """Test MFAValidation model validation"""
        mfa_validation = MFAValidation(token="123456")
        assert mfa_validation.token == "123456"

    @pytest.mark.asyncio
    async def test_concurrent_mfa_verification(self, mock_redis_client, mock_security_audit_logger):
        """Test concurrent MFA verification"""
        import asyncio

        username = "testuser"
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        valid_token = totp.now()

        mock_redis_client.get.return_value = secret

        async def verify_mfa_concurrent():
            return await verify_mfa(username, valid_token)

        # Run multiple verifications concurrently
        tasks = [verify_mfa_concurrent() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # All should be successful
        assert all(results)

    def test_password_hashing_consistency(self):
        """Test that password hashing is consistent"""
        password = "test_password"

        # Hash the same password multiple times
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        hash3 = get_password_hash(password)

        # Hashes should be different (due to salt)
        assert hash1 != hash2
        assert hash2 != hash3
        assert hash1 != hash3

        # But all should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
        assert verify_password(password, hash3)

    def test_token_expiration_handling(self, mock_security_audit_logger):
        """Test token expiration handling"""
        data = {"sub": "testuser"}

        # Create token that expires in the past
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta=expires_delta)

        # Token should be expired
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(
                token,
                security_settings.JWT_SECRET_KEY,
                algorithms=[security_settings.JWT_ALGORITHM]
            )

    @pytest.mark.asyncio
    async def test_mfa_token_time_sensitivity(self, mock_redis_client, mock_security_audit_logger):
        """Test MFA token time sensitivity"""
        username = "testuser"
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)

        mock_redis_client.get.return_value = secret

        # Get current valid token
        current_token = totp.now()

        # Should verify successfully
        assert await verify_mfa(username, current_token)

        # Test with token from different time window (should fail)
        import time
        time.sleep(31)  # Wait for next time window

        # The old token should now be invalid
        assert not await verify_mfa(username, current_token)

        # But a new token should work
        new_token = totp.now()
        assert await verify_mfa(username, new_token)

    @pytest.mark.asyncio
    async def test_authentication_error_logging(self, mock_security_audit_logger):
        """Test that authentication errors are logged"""
        invalid_token = "invalid.token.here"
        security_scopes = Mock()
        security_scopes.scopes = ["read"]
        security_scopes.scope_str = "read"

        try:
            await get_current_user(security_scopes, invalid_token)
        except HTTPException:
            pass

        # Check that error was logged
        mock_security_audit_logger.log_audit_event.assert_called()
        call_args = mock_security_audit_logger.log_audit_event.call_args
        assert call_args[1]["action"] == "token_validation"
