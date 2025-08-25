from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from app.core.config import settings
from app.services.email import email_service
from app.db.session import get_db
from app.models import User

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        pass  # Database operations will use session from dependency injection

    async def get_db_session(self):
        """Get database session."""
        async for session in get_db():
            yield session
            break

    async def create_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "info",
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new notification."""
        session = self.get_db_session()
        try:
            notification_id = str(uuid.uuid4())
            created_at = datetime.utcnow()

            # TODO: Replace with actual database insertion
            # For now, simulate the database operation
            notification = {
                "id": notification_id,
                "user_id": user_id,
                "title": title,
                "message": message,
                "type": notification_type,
                "data": data or {},
                "read": False,
                "created_at": created_at.isoformat()
            }

            logger.info(f"Created notification {notification_id} for user {user_id}")
            return notification
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()

    async def get_user_notifications(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get notifications for a user."""
        session = self.get_db_session()
        try:
            # TODO: Replace with actual database query
            # For now, return empty list (simulating no notifications)
            user_notifications = []

            logger.info(f"Retrieved {len(user_notifications)} notifications for user {user_id}")
            return user_notifications[offset:offset + limit]
        except Exception as e:
            logger.error(f"Error getting notifications: {str(e)}")
            return []
        finally:
            session.close()

    async def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read."""
        for notification in self.notifications_db:
            if notification["id"] == notification_id and notification["user_id"] == user_id:
                notification["read"] = True
                logger.info(f"Marked notification {notification_id} as read")
                return True
        return False

    async def mark_all_notifications_read(self, user_id: int) -> int:
        """Mark all notifications for a user as read."""
        count = 0
        for notification in self.notifications_db:
            if notification["user_id"] == user_id and not notification["read"]:
                notification["read"] = True
                count += 1

        logger.info(f"Marked {count} notifications as read for user {user_id}")
        return count

    async def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Delete a notification."""
        for i, notification in enumerate(self.notifications_db):
            if notification["id"] == notification_id and notification["user_id"] == user_id:
                del self.notifications_db[i]
                logger.info(f"Deleted notification {notification_id}")
                return True
        return False

    async def send_email_notification(
        self,
        user_email: str,
        subject: str,
        message: str,
        html_message: Optional[str] = None
    ) -> bool:
        """Send an email notification."""
        if html_message is None:
            html_message = f"<p>{message}</p>"

        return await email_service.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_message,
            text_content=message
        )

    async def notify_user_login(self, user_id: int, user_email: str, username: str) -> None:
        """Send login notification."""
        await self.create_notification(
            user_id=user_id,
            title="New Login Detected",
            message=f"New login detected for your account {username}",
            notification_type="security",
            data={"event": "login", "timestamp": datetime.utcnow().isoformat()}
        )

    async def notify_password_change(self, user_id: int, user_email: str, username: str) -> None:
        """Send password change notification."""
        await self.create_notification(
            user_id=user_id,
            title="Password Changed",
            message="Your password has been successfully changed",
            notification_type="security",
            data={"event": "password_change", "timestamp": datetime.utcnow().isoformat()}
        )

        # Also send email notification
        await self.send_email_notification(
            user_email=user_email,
            subject="Password Changed - Samoey Copilot",
            message="Your Samoey Copilot password has been successfully changed.",
            html_message="<h2>Password Changed</h2><p>Your Samoey Copilot password has been successfully changed.</p>"
        )

    async def notify_feature_update(self, user_id: int, user_email: str, feature_name: str, description: str) -> None:
        """Send feature update notification."""
        await self.create_notification(
            user_id=user_id,
            title=f"New Feature: {feature_name}",
            message=description,
            notification_type="feature",
            data={"event": "feature_update", "feature": feature_name}
        )

    async def get_notification_stats(self, user_id: int) -> Dict[str, Any]:
        """Get notification statistics for a user."""
        user_notifications = [
            notif for notif in self.notifications_db
            if notif["user_id"] == user_id
        ]

        total = len(user_notifications)
        unread = len([notif for notif in user_notifications if not notif["read"]])

        # Count by type
        by_type = {}
        for notif in user_notifications:
            notif_type = notif["type"]
            by_type[notif_type] = by_type.get(notif_type, 0) + 1

        return {
            "total": total,
            "unread": unread,
            "read": total - unread,
            "by_type": by_type
        }

# Global notification service instance
