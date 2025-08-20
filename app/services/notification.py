import logging
logger = logging.getLogger(__name__)

class NotificationService:
    async def get_user_notifications(self, user_id: int, skip: int = 0, limit: int = 100):
        """Get user notifications."""
        return []

    async def mark_notifications_read(self, user_id: int, notification_ids: list):
        """Mark notifications as read."""
        logger.info(f"Notifications marked as read for user {user_id}")

    async def delete_notification(self, user_id: int, notification_id: str) -> bool:
        """Delete notification."""
        logger.info(f"Notification {notification_id} deleted for user {user_id}")
        return True

notification_service = NotificationService()
