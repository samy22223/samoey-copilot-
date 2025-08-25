import secrets
import uuid
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.db.session import get_db_session
from app.core.security import create_access_token, create_refresh_token
from app.core.config import settings
from app.core.redis import redis_client
import logging

logger = logging.getLogger(__name__)

class AutoAPIKeyService:
    """
    Auto-generated API key and token management service.
    No external API keys required - everything is self-generated.
    """

    def __init__(self):
        self.api_key_length = getattr(settings, 'API_KEY_LENGTH', 64)
        self.token_expire_days = getattr(settings, 'TOKEN_EXPIRE_DAYS', 30)
        self.free_tier_limits = {
            "api_calls_per_day": getattr(settings, 'FREE_TIER_API_CALLS_PER_DAY', 10000),
            "messages_per_conversation": getattr(settings, 'FREE_TIER_MESSAGES_PER_CONVERSATION', 1000),
            "conversations_per_user": getattr(settings, 'FREE_TIER_CONVERSATIONS_PER_USER', 100),
            "file_storage_mb": getattr(settings, 'FREE_TIER_FILE_STORAGE_MB', 1000),
            "model_downloads": getattr(settings, 'FREE_TIER_MODEL_DOWNLOADS', 50),
            "concurrent_requests": getattr(settings, 'FREE_TIER_CONCURRENT_REQUESTS', 10)
        }

    def generate_secure_api_key(self, prefix: str = "sk") -> str:
        """
        Generate a cryptographically secure API key.
        Format: prefix-randomstring
        """
        # Generate random bytes and convert to URL-safe base64
        random_bytes = secrets.token_bytes(self.api_key_length)
        random_string = secrets.token_urlsafe(self.api_key_length)

        # Create API key with prefix
        api_key = f"{prefix}-{random_string}"

        # Add checksum for validation
        checksum = hashlib.sha256(api_key.encode()).hexdigest()[:8]
        final_key = f"{api_key}-{checksum}"

        return final_key

    def generate_secure_token(self, user_id: str) -> str:
        """
        Generate a secure random token for internal use.
        """
        return secrets.token_urlsafe(64)

    async def generate_user_api_key(self, user_id: str, key_name: str = "Auto-generated API Key") -> Dict[str, Any]:
        """
        Generate API key for a user automatically.
        """
        try:
            # Generate secure API key
            api_key = self.generate_secure_api_key()

            # Generate key metadata
            key_data = {
                "user_id": user_id,
                "key_name": key_name,
                "api_key": api_key,
                "key_hash": hashlib.sha256(api_key.encode()).hexdigest(),
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=self.token_expire_days)).isoformat(),
                "last_used": None,
                "usage_count": 0,
                "is_active": True,
                "tier": "free",
                "limits": self.free_tier_limits
            }

            # Store API key in Redis for fast access
            redis_key = f"api_key:{key_data['key_hash']}"
            await redis_client.setex(
                redis_key,
                timedelta(days=self.token_expire_days).total_seconds(),
                json.dumps(key_data)
            )

            # Store user's API keys list
            user_keys_key = f"user_api_keys:{user_id}"
            user_keys = await redis_client.get(user_keys_key)
            keys_list = json.loads(user_keys) if user_keys else []
            keys_list.append({
                "key_hash": key_data['key_hash'],
                "key_name": key_name,
                "created_at": key_data['created_at'],
                "is_active": True
            })
            await redis_client.setex(
                user_keys_key,
                timedelta(days=365).total_seconds(),  # Keep for 1 year
                json.dumps(keys_list)
            )

            logger.info(f"Generated API key for user {user_id}")

            return {
                "api_key": api_key,
                "key_name": key_name,
                "created_at": key_data['created_at'],
                "expires_at": key_data['expires_at'],
                "tier": "free",
                "limits": self.free_tier_limits
            }

        except Exception as e:
            logger.error(f"Error generating API key for user {user_id}: {str(e)}")
            raise

    async def auto_generate_tokens(self, user_id: str) -> Dict[str, Any]:
        """
        Auto-generate access and refresh tokens for user.
        """
        try:
            # Generate access token
            access_token = create_access_token(
                data={"user_id": user_id, "auto_generated": True},
                expires_delta=timedelta(minutes=60 * 24 * 8)  # 8 days
            )

            # Generate refresh token
            refresh_token = create_refresh_token(
                data={"user_id": user_id, "auto_generated": True},
                expires_delta=timedelta(minutes=60 * 24 * 30)  # 30 days
            )

            # Store tokens in Redis
            token_data = {
                "user_id": user_id,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "created_at": datetime.now().isoformat(),
                "access_expires_at": (datetime.now() + timedelta(days=8)).isoformat(),
                "refresh_expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
                "is_active": True
            }

            token_key = f"user_tokens:{user_id}"
            await redis_client.setex(
                token_key,
                timedelta(days=30).total_seconds(),
                json.dumps(token_data)
            )

            logger.info(f"Generated tokens for user {user_id}")

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 60 * 60 * 24 * 8,  # 8 days in seconds
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating tokens for user {user_id}: {str(e)}")
            raise

    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate API key and return key data if valid.
        """
        try:
            # Calculate key hash
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            # Get key data from Redis
            redis_key = f"api_key:{key_hash}"
            key_data_json = await redis_client.get(redis_key)

            if not key_data_json:
                return None

            key_data = json.loads(key_data_json)

            # Check if key is active
            if not key_data.get("is_active", True):
                return None

            # Check if key is expired
            expires_at = datetime.fromisoformat(key_data["expires_at"])
            if datetime.now() > expires_at:
                return None

            # Update last used timestamp
            key_data["last_used"] = datetime.now().isoformat()
            key_data["usage_count"] = key_data.get("usage_count", 0) + 1
            await redis_client.setex(
                redis_key,
                (expires_at - datetime.now()).total_seconds(),
                json.dumps(key_data)
            )

            return key_data

        except Exception as e:
            logger.error(f"Error validating API key: {str(e)}")
            return None

    async def get_user_api_keys(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all API keys for a user.
        """
        try:
            user_keys_key = f"user_api_keys:{user_id}"
            user_keys_json = await redis_client.get(user_keys_key)

            if not user_keys_json:
                return []

            keys_list = json.loads(user_keys_json)
            return keys_list

        except Exception as e:
            logger.error(f"Error getting API keys for user {user_id}: {str(e)}")
            return []

    async def revoke_api_key(self, user_id: str, key_hash: str) -> bool:
        """
        Revoke an API key.
        """
        try:
            # Remove from Redis
            redis_key = f"api_key:{key_hash}"
            await redis_client.delete(redis_key)

            # Update user's keys list
            user_keys_key = f"user_api_keys:{user_id}"
            user_keys_json = await redis_client.get(user_keys_key)

            if user_keys_json:
                keys_list = json.loads(user_keys_json)
                for key_info in keys_list:
                    if key_info["key_hash"] == key_hash:
                        key_info["is_active"] = False
                        break

                await redis_client.setex(
                    user_keys_key,
                    timedelta(days=365).total_seconds(),
                    json.dumps(keys_list)
                )

            logger.info(f"Revoked API key for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error revoking API key for user {user_id}: {str(e)}")
            return False

    async def check_rate_limit(self, user_id: str, action: str) -> Dict[str, Any]:
        """
        Check if user is within free tier rate limits.
        """
        try:
            # Get current usage
            usage_key = f"user_usage:{user_id}:{action}:{datetime.now().strftime('%Y-%m-%d')}"
            usage_json = await redis_client.get(usage_key)
            current_usage = int(usage_json) if usage_json else 0

            # Get limit
            limit = self.free_tier_limits.get(action, 1000)

            # Check if within limit
            remaining = max(0, limit - current_usage)
            is_within_limit = remaining > 0

            # Update usage if within limit
            if is_within_limit:
                await redis_client.setex(
                    usage_key,
                    timedelta(days=1).total_seconds(),  # Reset daily
                    str(current_usage + 1)
                )

            return {
                "is_within_limit": is_within_limit,
                "current_usage": current_usage,
                "limit": limit,
                "remaining": remaining,
                "action": action
            }

        except Exception as e:
            logger.error(f"Error checking rate limit for user {user_id}: {str(e)}")
            return {
                "is_within_limit": True,  # Allow on error
                "current_usage": 0,
                "limit": self.free_tier_limits.get(action, 1000),
                "remaining": self.free_tier_limits.get(action, 1000),
                "action": action
            }

    async def get_user_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive usage statistics for a user.
        """
        try:
            stats = {}

            for action in self.free_tier_limits.keys():
                # Get today's usage
                usage_key = f"user_usage:{user_id}:{action}:{datetime.now().strftime('%Y-%m-%d')}"
                usage_json = await redis_client.get(usage_key)
                today_usage = int(usage_json) if usage_json else 0

                # Get limit
                limit = self.free_tier_limits.get(action, 1000)

                stats[action] = {
                    "today_usage": today_usage,
                    "limit": limit,
                    "remaining": max(0, limit - today_usage),
                    "percentage_used": (today_usage / limit) * 100 if limit > 0 else 0
                }

            return stats

        except Exception as e:
            logger.error(f"Error getting usage stats for user {user_id}: {str(e)}")
            return {}

    async def generate_system_credentials(self) -> Dict[str, Any]:
        """
        Generate system-level credentials for internal services.
        """
        try:
            # Generate system API key
            system_api_key = self.generate_secure_api_key("sys")

            # Generate system tokens
            system_token = secrets.token_urlsafe(128)

            # Store system credentials
            system_creds = {
                "api_key": system_api_key,
                "token": system_token,
                "created_at": datetime.now().isoformat(),
                "type": "system",
                "permissions": ["internal", "admin", "model_management"]
            }

            await redis_client.setex(
                "system_credentials",
                timedelta(days=365).total_seconds(),
                json.dumps(system_creds)
            )

            logger.info("Generated system credentials")

