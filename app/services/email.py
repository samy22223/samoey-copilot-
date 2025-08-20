import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from jinja2 import Template
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email to recipient."""
        try:
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.smtp_user
            message['To'] = to_email

            if text_content:
                text_part = MIMEText(text_content, 'plain')
                message.attach(text_part)

            html_part = MIMEText(html_content, 'html')
            message.attach(html_part)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    async def send_welcome_email(self, to_email: str, username: str) -> bool:
        """Send welcome email to new user."""
        template = Template("""
        <h2>Welcome to Samoey Copilot, {{ username }}!</h2>
        <p>Thank you for joining our platform. We're excited to have you on board.</p>
        <p>Get started by exploring our AI-powered features and tools.</p>
        <p>If you have any questions, don't hesitate to reach out to our support team.</p>
        <p>Best regards,<br>The Samoey Copilot Team</p>
        """)

        html_content = template.render(username=username)
        text_content = f"Welcome to Samoey Copilot, {username}! Thank you for joining our platform."

        return await self.send_email(
            to_email=to_email,
            subject="Welcome to Samoey Copilot!",
            html_content=html_content,
            text_content=text_content
        )

    async def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset email."""
        reset_link = f"https://yourdomain.com/reset-password?token={reset_token}"

        template = Template("""
        <h2>Password Reset Request</h2>
        <p>You requested a password reset for your Samoey Copilot account.</p>
        <p>Click the link below to reset your password:</p>
        <p><a href="{{ reset_link }}">Reset Password</a></p>
        <p>If you didn't request this, please ignore this email.</p>
        <p>Best regards,<br>The Samoey Copilot Team</p>
        """)

        html_content = template.render(reset_link=reset_link)
        text_content = f"Reset your password here: {reset_link}"

        return await self.send_email(
            to_email=to_email,
            subject="Password Reset Request",
            html_content=html_content,
            text_content=text_content
        )

# Global email service instance
email_service = EmailService()
