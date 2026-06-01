"""
Handles sending email notifications via SendGrid.
"""

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from config.settings import SENDGRID_API_KEY, SENDER_EMAIL, SENDER_NAME


class EmailSender:
    """Sends maintenance reminder emails using SendGrid."""
    
    def __init__(self):
        """Initialize SendGrid client."""
        if not SENDGRID_API_KEY:
            raise ValueError("❌ SENDGRID_API_KEY not set in environment variables!")
        
        self.client = SendGridAPIClient(SENDGRID_API_KEY)
        self.from_email = Email(SENDER_EMAIL, SENDER_NAME)
    
    def send_reminder(self, asset_info, reminder_type='today'):
        """
        Send a maintenance reminder email.
        
        Args:
            asset_info: Dictionary containing asset details
            reminder_type: 'today' or '7days'
        """
        # Extract information from asset record
        asset_name = asset_info.get('Asset Name', 'Unknown Asset')
        asset_id = asset_info.get('Asset ID', 'N/A')
        maintenance_date = asset_info.get('Maintenance Date', 'N/A')
        pic_email = asset_info.get('PIC Email', '')
        pic_name = asset_info.get('PIC Name', 'Team Member')
        
        # Validate email
        if not pic_email or '@' not in pic_email:
            print(f"⚠️ Invalid email for {asset_name}: {pic_email}")
            return False
        
        # Create email subject and body based on reminder type
        if reminder_type == 'today':
            subject = f"🔔 URGENT: Maintenance Due TODAY - {asset_name}"
            urgency_text = "**TODAY**"
            urgency_color = "#dc3545"  # Red
        else:
            subject = f"⏰ Reminder: Maintenance Due in 7 Days - {asset_name}"
            urgency_text = "in 7 days"
            urgency_color = "#ffc107"  # Yellow
        
        # HTML email body
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {urgency_color}; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 5px 5px; }}
                .asset-details {{ background-color: white; padding: 20px; border-left: 4px solid {urgency_color}; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #888; }}
                .button {{ background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Maintenance Reminder</h1>
                </div>
                <div class="content">
                    <p>Hello {pic_name},</p>
                    
                    <p>This is an automated reminder that maintenance is due <strong>{urgency_text}</strong> for the following asset:</p>
                    
                    <div class="asset-details">
                        <p><strong>Asset ID:</strong> {asset_id}</p>
                        <p><strong>Asset Name:</strong> {asset_name}</p>
                        <p><strong>Scheduled Maintenance Date:</strong> {maintenance_date}</p>
                        <p><strong>Person in Charge:</strong> {pic_name}</p>
                    </div>
                    
                    <p><strong>Action Required:</strong></p>
                    <ul>
                        <li>Review maintenance checklist</li>
                        <li>Prepare necessary tools and spare parts</li>
                        <li>Schedule downtime if required</li>
                        <li>Update status after completion</li>
                    </ul>
                    
                    <p>If you have any questions or need to reschedule, please contact the maintenance team immediately.</p>
                    
                    <div class="footer">
                        <p>This is an automated message from the Maintenance Reminder System.</p>
                        <p>Please do not reply to this email.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version (fallback)
        plain_content = f"""
        Maintenance Reminder
        
        Hello {pic_name},
        
        This is an automated reminder that maintenance is due {urgency_text} for:
        
        Asset ID: {asset_id}
        Asset Name: {asset_name}
        Scheduled Date: {maintenance_date}
        
        Please ensure all necessary preparations are completed.
        
        ---
        Automated message from Maintenance Reminder System
        """
        
        # Create the email
        message = Mail(
            from_email=self.from_email,
            to_emails=To(pic_email),
            subject=subject,
            plain_text_content=Content("text/plain", plain_content),
            html_content=Content("text/html", html_content)
        )
        
        # Send the email
        try:
            response = self.client.send(message)
            print(f"✅ Email sent to {pic_email} for {asset_name} (Status: {response.status_code})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {pic_email}: {str(e)}")
            return False