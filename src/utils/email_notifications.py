"""
Email notification utility for contact messages
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailNotificationManager:
    """Email notification manager for contact messages"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('SMTP_FROM_EMAIL', self.smtp_username)
        self.to_email = os.getenv('CONTACT_NOTIFICATION_EMAIL', 'admin@yourserver.com')
        self.enabled = os.getenv('EMAIL_NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
    
    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        return bool(self.smtp_username and self.smtp_password and self.to_email and self.enabled)
    
    async def send_contact_notification(self, contact_data: dict) -> bool:
        """Send email notification for new contact message"""
        if not self.is_configured():
            logger.info("Email notifications not configured, skipping...")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = self.to_email
            msg['Subject'] = f"📧 New Contact Message: {contact_data['subject']}"
            
            # Create email body
            body = f"""
            New contact message received on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            
            📋 CONTACT DETAILS:
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            
            👤 Name: {contact_data['first_name']} {contact_data['last_name']}
            📧 Email: {contact_data['email']}
            🏢 Company: {contact_data.get('company', 'Not provided')}
            📌 Subject: {contact_data['subject']}
            
            💬 MESSAGE:
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            {contact_data['message']}
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            
            🔗 To reply or manage this message, visit your admin dashboard:
            {os.getenv('BASE_URL', 'http://localhost:3111')}/admin/contact-messages
            
            Best regards,
            Trigger Deploy Server
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            text = msg.as_string()
            server.sendmail(self.from_email, self.to_email, text)
            server.quit()
            
            logger.info(f"Contact notification email sent to {self.to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send contact notification email: {e}")
            return False


# Global instance
email_manager = EmailNotificationManager()

async def send_contact_notification_email(contact_data: dict) -> bool:
    """Send contact notification email"""
    return await email_manager.send_contact_notification(contact_data)
