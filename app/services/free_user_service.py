import secrets
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.db.session import get_db_session
from app.models import User
from app.core.security import get_password_hash, verify_password
from app.core.config import settings
from app.core.redis import redis_client
from .auto_api_key_service import AutoAPIKeyService
import logging

logger = logging.getLogger(__name__)

class FreeUserService:
    """
    Free user registration and management service.
    No admin intervention required - completely self-service.
    """

    def __init__(self):
        self.auto_api_key_service = AutoAPIKeyService()
        self.default_user_limits = {
            "max_conversations": 100,
            "max_messages_per_conversation": 1000,
            "max_file_storage_mb": 1000,
            "max_api_keys": 5,
            "max_model_downloads": 50,
            "max_concurrent_requests": 10
        }

    async def self_register_user(self, email: str, username: str, password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Auto-register user with generated credentials and setup.
        """
        try:
            # Check if user already exists
            existing_user = await self._get_user_by_email(email)
            if existing_user:
                raise ValueError("User with this email already exists")

            existing_user = await self._get_user_by_username(username)
            if existing_user:
                raise ValueError("Username already taken")

            # Create user
            user = await self._create_user(
                email=email,
                username=username,
                password=password,
                full_name=full_name or username
            )

            # Generate API key automatically
            api_key_data = await self.auto_api_key_service.generate_user_api_key(
                user.id,
                "Auto-generated API Key"
            )

            # Generate tokens automatically
            tokens = await self.auto_api_key_service.auto_generate_tokens(user.id)

            # Set up user workspace
            workspace_setup = await self._setup_user_workspace(user.id)

            # Set up free tier limits
            await self._setup_free_tier_limits(user.id)

            logger.info(f"Auto-registered user: {email}")

            return {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat()
                },
                "api_key": api_key_data["api_key"],
                "tokens": tokens,
                "workspace_setup": workspace_setup,
                "limits": self.default_user_limits,
                "message": "Welcome! Your free Samoey Copilot account is ready to use.",
                "next_steps": [
                    "Use your API key to access the API",
                    "Download free AI models from the dashboard",
                    "Start creating conversations and projects",
                    "Explore the free tier features"
                ]
            }

        except Exception as e:
            logger.error(f"Error in self-registration for {email}: {str(e)}")
            raise

    async def quick_register_user(self, email: str) -> Dict[str, Any]:
        """
        Quick registration with minimal information - auto-generates everything.
        """
        try:
            # Generate random username and password
            username = f"user_{secrets.token_hex(8)}"
            password = secrets.token_urlsafe(16)
            full_name = email.split('@')[0]

            # Register user
            result = await self.self_register_user(email, username, password, full_name)

            # Add auto-generated credentials to result
            result["auto_generated_credentials"] = {
                "username": username,
                "password": password,
                "warning": "Save these credentials securely - they cannot be recovered"
            }

            return result

        except Exception as e:
            logger.error(f"Error in quick registration for {email}: {str(e)}")
            raise

    async def auto_login_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Auto-login user and generate fresh tokens.
        """
        try:
            # Get user
            user = await self._get_user_by_email(email)
            if not user:
                raise ValueError("User not found")

            # Verify password
            if not verify_password(password, user.hashed_password):
                raise ValueError("Invalid credentials")

            # Generate fresh tokens
            tokens = await self.auto_api_key_service.auto_generate_tokens(user.id)

            # Get user's API keys
            api_keys = await self.auto_api_key_service.get_user_api_keys(user.id)

            # Get usage stats
            usage_stats = await self.auto_api_key_service.get_user_usage_stats(user.id)

            logger.info(f"Auto-login successful for user: {email}")

            return {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "is_active": user.is_active
                },
                "tokens": tokens,
                "api_keys_count": len(api_keys),
                "usage_stats": usage_stats,
                "message": "Login successful"
            }

        except Exception as e:
            logger.error(f"Error in auto-login for {email}: {str(e)}")
            raise

    async def setup_free_account(self, user_id: str) -> Dict[str, Any]:
        """
        Set up free account features for existing user.
        """
        try:
            setup_results = {}

            # Generate API key if user doesn't have one
            api_keys = await self.auto_api_key_service.get_user_api_keys(user_id)
            if not api_keys:
                api_key_data = await self.auto_api_key_service.generate_user_api_key(
                    user_id,
                    "Free Tier API Key"
                )
                setup_results["api_key_generated"] = api_key_data["api_key"]

            # Set up workspace
            workspace_setup = await self._setup_user_workspace(user_id)
            setup_results["workspace_setup"] = workspace_setup

            # Set up free tier limits
            await self._setup_free_tier_limits(user_id)
            setup_results["free_tier_setup"] = "completed"

            # Generate welcome message
            welcome_data = await self._generate_welcome_message(user_id)
            setup_results["welcome_message"] = welcome_data

            logger.info(f"Set up free account for user {user_id}")

            return {
                "setup_completed": True,
                "results": setup_results,
                "message": "Free account setup completed successfully"
            }

        except Exception as e:
            logger.error(f"Error setting up free account for user {user_id}: {str(e)}")
            raise

    async def upgrade_to_free_tier(self, user_id: str) -> Dict[str, Any]:
        """
        Upgrade user to free tier (if they were on limited tier).
        """
        try:
            # Remove any limitations
            await self._remove_user_limitations(user_id)

            # Set up free tier limits
            await self._setup_free_tier_limits(user_id)

            # Generate new API key with free tier access
            api_key_data = await self.auto_api_key_service.generate_user_api_key(
                user_id,
                "Free Tier Upgrade API Key"
            )

            logger.info(f"Upgraded user {user_id} to free tier")

            return {
                "upgrade_completed": True,
                "new_api_key": api_key_data["api_key"],
                "limits": self.default_user_limits,
                "message": "Successfully upgraded to free tier"
            }

        except Exception as e:
            logger.error(f"Error upgrading user {user_id} to free tier: {str(e)}")
            raise

    async def get_free_tier_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's free tier status and remaining usage.
        """
        try:
            # Get usage stats
            usage_stats = await self.auto_api_key_service.get_user_usage_stats(user_id)

            # Get API keys
            api_keys = await self.auto_api_key_service.get_user_api_keys(user_id)

            # Calculate overall status
            total_usage = sum(stats["today_usage"] for stats in usage_stats.values())
            total_limit = sum(stats["limit"] for stats in usage_stats.values())
            overall_percentage = (total_usage / total_limit * 100) if total_limit > 0 else 0

            # Determine tier status
            tier_status = "active"
            if overall_percentage > 90:
                tier_status = "nearing_limit"
            elif overall_percentage >= 100:
                tier_status = "limit_reached"

            return {
                "tier": "free",
                "status": tier_status,
                "usage_stats": usage_stats,
                "overall_percentage": overall_percentage,
                "api_keys_count": len(api_keys),
                "limits": self.default_user_limits,
                "recommendations": self._get_usage_recommendations(usage_stats)
            }

        except Exception as e:
            logger.error(f"Error getting free tier status for user {user_id}: {str(e)}")
            return {
                "tier": "free",
                "status": "error",
                "usage_stats": {},
                "overall_percentage": 0,
                "api_keys_count": 0,
                "limits": self.default_user_limits,
                "recommendations": []
            }

    # Helper methods

    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        async with get_db_session() as db:
            return db.query(User).filter(User.email == email).first()

    async def _get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        async with get_db_session() as db:
            return db.query(User).filter(User.username == username).first()

    async def _create_user(self, email: str, username: str, password: str, full_name: str) -> User:
        """Create new user."""
        async with get_db_session() as db:
            hashed_password = get_password_hash(password)
            user = User(
                email=email,
                username=username,
                hashed_password=hashed_password,
                full_name=full_name,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

    async def _setup_user_workspace(self, user_id: str) -> Dict[str, Any]:
        """Set up user workspace with default projects and settings."""
        try:
            workspace_data = {
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "default_projects": ["Welcome Project", "AI Testing Ground"],
                "settings": {
                    "theme": "auto",
                    "language": "en",
                    "notifications_enabled": True,
                    "auto_save": True
                },
                "storage": {
                    "used_mb": 0,
                    "allocated_mb": self.default_user_limits["max_file_storage_mb"]
                }
            }

            # Store workspace data in Redis
            workspace_key = f"user_workspace:{user_id}"
            await redis_client.setex(
                workspace_key,
                timedelta(days=365).total_seconds(),
                json.dumps(workspace_data)
            )

            return {
                "workspace_created": True,
                "default_projects": workspace_data["default_projects"],
                "settings": workspace_data["settings"]
            }

        except Exception as e:
            logger.error(f"Error setting up workspace for user {user_id}: {str(e)}")
            return {"workspace_created": False, "error": str(e)}

    async def _setup_free_tier_limits(self, user_id: str) -> None:
        """Set up free tier limits for user."""
        try:
            limits_key = f"user_limits:{user_id}"
            limits_data = {
                **self.default_user_limits,
                "tier": "free",
                "setup_at": datetime.now().isoformat(),
                "reset_interval": "daily"
            }

            await redis_client.setex(
                limits_key,
                timedelta(days=365).total_seconds(),
                json.dumps(limits_data)
            )

        except Exception as e:
            logger.error(f"Error setting up free tier limits for user {user_id}: {str(e)}")

    async def _remove_user_limitations(self, user_id: str) -> None:
        """Remove any user limitations."""
        try:
            # Clear any limitation keys
            limitation_keys = [
                f"user_limits:{user_id}",
                f"user_restrictions:{user_id}",
                f"user_tier:{user_id}"
            ]

            for key in limitation_keys
