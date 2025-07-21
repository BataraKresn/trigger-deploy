"""
Email Notification Service
Handles email notifications for deployment events and alerts
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending email notifications"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
        self.from_name = os.getenv('FROM_NAME', 'Trigger Deploy Server')
        self.enabled = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
        
        if not self.smtp_username or not self.smtp_password:
            logger.warning("Email credentials not configured. Email notifications disabled.")
            self.enabled = False
    
    def _create_smtp_connection(self):
        """Create SMTP connection"""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            return server
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            raise
    
    def send_email(self, to_emails: List[str], subject: str, body: str, 
                   html_body: Optional[str] = None, attachments: Optional[List[str]] = None) -> bool:
        """Send email notification"""
        if not self.enabled:
            logger.info("Email notifications disabled")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Add text body
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Add HTML body if provided
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(file_path)}'
                            )
                            msg.attach(part)
            
            # Send email
            with self._create_smtp_connection() as server:
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to: {', '.join(to_emails)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_deployment_success_notification(self, deployment_data: Dict[str, Any], 
                                           recipients: List[str]) -> bool:
        """Send deployment success notification"""
        server_name = deployment_data.get('server_name', 'Unknown Server')
        service_name = deployment_data.get('service_name', 'Unknown Service')
        duration = deployment_data.get('duration', 0)
        triggered_by = deployment_data.get('triggered_by', 'System')
        timestamp = deployment_data.get('created_at', datetime.now())
        
        subject = f"✅ Deployment Successful - {service_name} on {server_name}"
        
        # Text body
        body = f"""
Deployment Completed Successfully!

Service: {service_name}
Server: {server_name}
Triggered by: {triggered_by}
Duration: {duration:.2f} seconds
Completed at: {timestamp}

This is an automated notification from Trigger Deploy Server.
"""
        
        # HTML body
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 24px;">✅ Deployment Successful</h1>
        </div>
        <div style="padding: 30px;">
            <h2 style="color: #28a745; margin-bottom: 20px;">Deployment Details</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #e9ecef;">
                    <td style="padding: 10px 0; font-weight: bold; color: #495057;">Service:</td>
                    <td style="padding: 10px 0; color: #6c757d;">{service_name}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e9ecef;">
                    <td style="padding: 10px 0; font-weight: bold; color: #495057;">Server:</td>
                    <td style="padding: 10px 0; color: #6c757d;">{server_name}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e9ecef;">
                    <td style="padding: 10px 0; font-weight: bold; color: #495057;">Triggered by:</td>
                    <td style="padding: 10px 0; color: #6c757d;">{triggered_by}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e9ecef;">
                    <td style="padding: 10px 0; font-weight: bold; color: #495057;">Duration:</td>
                    <td style="padding: 10px 0; color: #6c757d;">{duration:.2f} seconds</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; font-weight: bold; color: #495057;">Completed at:</td>
                    <td style="padding: 10px 0; color: #6c757d;">{timestamp}</td>
                </tr>
            </table>
        </div>
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; text-align: center; color: #6c757d; font-size: 14px;">
            This is an automated notification from Trigger Deploy Server
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(recipients, subject, body, html_body)
    
    def send_deployment_failure_notification(self, deployment_data: Dict[str, Any], 
                                           recipients: List[str]) -> bool:
        """Send deployment failure notification"""
        server_name = deployment_data.get('server_name', 'Unknown Server')
        service_name = deployment_data.get('service_name', 'Unknown Service')
        error_output = deployment_data.get('error_output', 'No error details available')
        triggered_by = deployment_data.get('triggered_by', 'System')
        timestamp = deployment_data.get('created_at', datetime.now())
        
        subject = f"❌ Deployment Failed - {service_name} on {server_name}"
        
        # Text body
        body = f"""
Deployment Failed!

Service: {service_name}
Server: {server_name}
Triggered by: {triggered_by}
Failed at: {timestamp}

Error Details:
{error_output}

Please check the deployment logs and server status.

This is an automated notification from Trigger Deploy Server.
"""
        
        # HTML body
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 24px;">❌ Deployment Failed</h1>
        </div>
        <div style="padding: 30px;">
            <h2 style="color: #dc3545; margin-bottom: 20px;">Deployment Details</h2>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr style="border-bottom: 1px solid #e9ecef;">
                    <td style="padding: 10px 0; font-weight: bold; color: #495057;">Service:</td>
                    <td style="padding: 10px 0; color: #6c757d;">{service_name}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e9ecef;">
                    <td style="padding: 10px 0; font-weight: bold; color: #495057;">Server:</td>
                    <td style="padding: 10px 0; color: #6c757d;">{server_name}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e9ecef;">
                    <td style="padding: 10px 0; font-weight: bold; color: #495057;">Triggered by:</td>
                    <td style="padding: 10px 0; color: #6c757d;">{triggered_by}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; font-weight: bold; color: #495057;">Failed at:</td>
                    <td style="padding: 10px 0; color: #6c757d;">{timestamp}</td>
                </tr>
            </table>
            <h3 style="color: #dc3545; margin-bottom: 10px;">Error Details:</h3>
            <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; padding: 15px; color: #721c24; font-family: monospace; white-space: pre-wrap;">{error_output}</div>
        </div>
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; text-align: center; color: #6c757d; font-size: 14px;">
            This is an automated notification from Trigger Deploy Server
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(recipients, subject, body, html_body)
    
    def send_server_alert_notification(self, alert_data: Dict[str, Any], 
                                     recipients: List[str]) -> bool:
        """Send server alert notification"""
        server_name = alert_data.get('server_name', 'Unknown Server')
        alert_type = alert_data.get('alert_type', 'Unknown Alert')
        severity = alert_data.get('severity', 'medium')
        message = alert_data.get('message', 'No details available')
        timestamp = alert_data.get('timestamp', datetime.now())
        
        severity_colors = {
            'low': '#28a745',
            'medium': '#ffc107', 
            'high': '#fd7e14',
            'critical': '#dc3545'
        }
        
        severity_icons = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠', 
            'critical': '🔴'
        }
        
        icon = severity_icons.get(severity, '⚠️')
        color = severity_colors.get(severity, '#6c757d')
        
        subject = f"{icon} {severity.upper()} Alert - {server_name}: {alert_type}"
        
        # Text body
        body = f"""
Server Alert Triggered!

Server: {server_name}
Alert Type: {alert_type}
Severity: {severity.upper()}
Timestamp: {timestamp}

Details:
{message}

Please investigate and take appropriate action.

This is an automated notification from Trigger Deploy Server.
"""
        
        # HTML body
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <div style="background: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 24px;">{icon} {severity.upper()} Alert</h1>
        </div>
        <div style="padding: 30px;">
            <h2 style="color: {color}; margin-bottom: 20px;">Alert Details</h2>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr style="border-bottom: 1px solid #e9ecef;">
                    <td style="padding: 10px 0; font-weight: bold; color: #495057;">Server:</td>
                    <td style="padding: 10px 0; color: #6c757d;">{server_name}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e9ecef;">
                    <td style="padding: 10px 0; font-weight: bold; color: #495057;">Alert Type:</td>
                    <td style="padding: 10px 0; color: #6c757d;">{alert_type}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e9ecef;">
                    <td style="padding: 10px 0; font-weight: bold; color: #495057;">Severity:</td>
                    <td style="padding: 10px 0; color: {color}; font-weight: bold;">{severity.upper()}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; font-weight: bold; color: #495057;">Timestamp:</td>
                    <td style="padding: 10px 0; color: #6c757d;">{timestamp}</td>
                </tr>
            </table>
            <h3 style="color: {color}; margin-bottom: 10px;">Details:</h3>
            <div style="background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 15px; color: #495057;">{message}</div>
        </div>
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; text-align: center; color: #6c757d; font-size: 14px;">
            This is an automated notification from Trigger Deploy Server
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(recipients, subject, body, html_body)
    
    def test_email_configuration(self, test_email: str) -> Dict[str, Any]:
        """Test email configuration"""
        try:
            if not self.enabled:
                return {
                    'success': False,
                    'error': 'Email notifications are disabled. Check configuration.'
                }
            
            subject = "🧪 Test Email - Trigger Deploy Server"
            body = """
This is a test email from Trigger Deploy Server.

If you received this email, your email configuration is working correctly!

Test details:
- SMTP Server: {self.smtp_server}:{self.smtp_port}
- From: {self.from_email}
- Timestamp: {datetime.now()}

Trigger Deploy Server Team
"""
            
            success = self.send_email([test_email], subject, body)
            
            if success:
                return {
                    'success': True,
                    'message': f'Test email sent successfully to {test_email}'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to send test email. Check logs for details.'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Email test failed: {str(e)}'
            }


# Global notification service instance
notification_service = EmailNotificationService()
