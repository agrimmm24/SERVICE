import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import Optional
from dotenv import load_dotenv

from enum import Enum

# Load sensitive environment variables
load_dotenv()

class SenderType(Enum):
    AUTH = "auth"
    NOTIFY = "notify"
    SUPPORT = "support"

# SMTP Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# Default Credentials
DEFAULT_USER = os.getenv("SMTP_USER", "noreply.servsync@gmail.com")
DEFAULT_PASS = os.getenv("SMTP_PASS", "")

# Specialized Credentials (fall back to default)
CREDENTIALS = {
    SenderType.AUTH: {
        "user": os.getenv("AUTH_USER", DEFAULT_USER),
        "pass": os.getenv("AUTH_PASS", DEFAULT_PASS),
        "display_name": "ServSync Security"
    },
    SenderType.NOTIFY: {
        "user": os.getenv("NOTIFY_USER", DEFAULT_USER),
        "pass": os.getenv("NOTIFY_PASS", DEFAULT_PASS),
        "display_name": "ServSync Notifications"
    },
    SenderType.SUPPORT: {
        "user": os.getenv("SUPPORT_USER", DEFAULT_USER),
        "pass": os.getenv("SUPPORT_PASS", DEFAULT_PASS),
        "display_name": "ServSync Support"
    }
}

def send_email(to_email: str, subject: str, body: str, html_body: Optional[str] = None, sender_type: SenderType = SenderType.NOTIFY):
    """
    Sends an email using SMTP with a specific sender identity.
    """
    config = CREDENTIALS.get(sender_type)
    user = config["user"]
    password = config["pass"]
    display_name = config["display_name"]

    if not password:
        print(f"--- MOCK EMAIL SENT [{sender_type.value.upper()}] ---")
        print(f"From: {display_name} <{user}>")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Body: {body[:100]}...")
        print(f"------------------------------------------")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{display_name} <{user}>"
        msg["To"] = to_email

        # Attach plain text
        part1 = MIMEText(body, "plain")
        msg.attach(part1)

        # Attach HTML if provided
        if html_body:
            part2 = MIMEText(html_body, "html")
            msg.attach(part2)

        # Connect and send
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(user, to_email, msg.as_string())
        
        return True
    except Exception as e:
        print(f"Error sending email [{sender_type.value}]: {e}")
        return False

def get_base_html(title: str, preheader: str, content_html: str, button_text: Optional[str] = None, button_url: Optional[str] = None):
    """
    Returns a creative HTML template with a professional background image.
    Uses a high-quality automotive background image for premium feel.
    """
    bg_image_url = "https://images.unsplash.com/photo-1486006920555-c77dcf18193c?q=80&w=1200&auto=format&fit=crop"
    
    button_html = ""
    if button_text and button_url:
        button_html = f"""
            <div style="margin-top: 30px;">
                <a href="{button_url}" style="display: inline-block; background-color: #dc2626; color: #ffffff; padding: 14px 40px; border-radius: 12px; text-decoration: none; font-weight: 900; text-transform: uppercase; font-size: 14px; letter-spacing: 1px; box-shadow: 0 4px 15px rgba(220, 38, 38, 0.4);">
                    {button_text}
                </a>
            </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;700&display=swap');
        </style>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Inter', sans-serif; background-color: #05060a; color: #ffffff;">
        <div style="display: none; max-height: 0px; overflow: hidden;">{preheader}</div>
        
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #05060a;">
            <tr>
                <td align="center" style="padding: 40px 0 60px 0;">
                    <!-- Wrapper Table -->
                    <table border="0" cellpadding="0" cellspacing="0" width="600" style="background-color: #0c0d12; border: 1px solid #1f2937; border-radius: 24px; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.5);">
                        
                        <!-- Header with Background Image -->
                        <tr>
                            <td align="center" style="position: relative; padding: 60px 40px; background-image: linear-gradient(rgba(12, 13, 18, 0.7), rgba(12, 13, 18, 0.95)), url('{bg_image_url}'); background-size: cover; background-position: center;">
                                <div style="font-family: 'Orbitron', sans-serif; letter-spacing: 4px; color: #dc2626; font-size: 14px; font-weight: 900; margin-bottom: 15px; text-transform: uppercase;">ServSync Terminal</div>
                                <h1 style="font-family: 'Orbitron', sans-serif; margin: 0; font-size: 36px; font-weight: 900; color: #ffffff; text-transform: uppercase;">{title}</h1>
                                <div style="height: 4px; width: 60px; background-color: #dc2626; margin: 20px auto 0 auto; border-radius: 2px;"></div>
                            </td>
                        </tr>

                        <!-- Content Area -->
                        <tr>
                            <td style="padding: 40px; text-align: center;">
                                <div style="color: #9ca3af; font-size: 16px; line-height: 1.8;">
                                    {content_html}
                                </div>
                                
                                {button_html}
                            </td>
                        </tr>

                        <!-- Footer Area -->
                        <tr>
                            <td style="padding: 40px; background-color: #08090d; border-top: 1px solid #1f2937; text-align: center;">
                                <div style="font-family: 'Orbitron', sans-serif; color: #374151; font-size: 10px; text-transform: uppercase; letter-spacing: 2px;">
                                    &copy; 2026 SERVSYNC SYSTEMS. ALL RIGHTS RESERVED.
                                </div>
                                <div style="margin-top: 10px; color: #1f2937; font-size: 9px;">
                                    AUTO-AUTH: SECURED-LINK-PROTOCOL-v4.0
                                </div>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

def send_verification_otp_email(user_email: str, user_name: str, otp_code: str):
    """Automated verification email with OTP code."""
    subject = "Verify Your ServSync Account - OTP"
    
    content = f"""
        <p>Hello <strong>{user_name}</strong>,</p>
        <p>Thank you for joining ServSync. Your account has been created, but requires email verification before you can access the terminal.</p>
        <div style="background-color: #05060a; border: 1px solid #dc2626; border-radius: 16px; padding: 30px; margin: 30px 0; display: inline-block;">
            <p style="color: #6b7280; font-size: 12px; font-weight: 900; text-transform: uppercase; margin: 0 0 10px 0; letter-spacing: 2px;">Verification OTP</p>
            <h2 style="font-family: monospace; color: #ffffff; font-size: 48px; font-weight: 900; margin: 0; letter-spacing: 8px;">{otp_code}</h2>
        </div>
        <p style="font-size: 14px; color: #4b5563;">This code expires in 15 minutes. Please enter this code on the verification screen to activate your account.</p>
    """
    
    html_content = get_base_html(
        title="Verification",
        preheader="Your one-time password for ServSync verification.",
        content_html=content,
        button_text="Verify Account",
        button_url="http://localhost:5173/signup"
    )
    
    plain_content = f"""
    Verify Your ServSync Account, {user_name}!
    
    Your account has been created. To activate it, please use the following One-Time Password (OTP):
    
    OTP: {otp_code}
    
    This code expires in 15 minutes.
    
    -- ServSync Systems
    """
    
    return send_email(user_email, subject, plain_content, html_content, sender_type=SenderType.AUTH)

def send_booking_update_email(customer_email: str, customer_name: str, booking_id: str, old_status: str, new_status: str):
    """Automated email notification for booking status changes."""
    subject = f"ServSync: Booking Status Updated to {new_status}"
    
    # ... (rest of html_content and plain_content logic omitted for brevity as it's large, but I will include it)
    # Actually I should be more precise.
    
    content = f"""
        <p>Hello <strong>{customer_name}</strong>,</p>
        <p>The status of your service booking <strong>(ID: {booking_id})</strong> has been updated.</p>
        
        <div style="background-color: #05060a; border: 1px solid #1f2937; border-radius: 16px; padding: 25px; margin: 30px 0; border-left: 4px solid #dc2626; text-align: left;">
            <p style="color: #6b7280; font-size: 10px; font-weight: 900; text-transform: uppercase; margin: 0 0 5px 0; letter-spacing: 1px;">Current Status</p>
            <div style="color: #dc2626; font-size: 24px; font-weight: 900; text-transform: uppercase;">{new_status}</div>
            <div style="color: #4b5563; font-size: 12px; margin-top: 5px;">Previous: {old_status}</div>
        </div>
        
        <p>Your vehicle is being handled by our premium care team. You can track real-time progress on your dashboard.</p>
    """
    
    html_content = get_base_html(
        title="Status Update",
        preheader=f"Booking {booking_id} status changed to {new_status}.",
        content_html=content,
        button_text="Track Progress",
        button_url="http://localhost:5173/dashboard"
    )
    
    plain_content = f"""
    Hello {customer_name},
    
    The status of your booking (ID: {booking_id}) has been updated from {old_status} to {new_status}.
    
    Track your progress here: http://localhost:5173/dashboard
    
    -- ServSync Systems
    """
    
    return send_email(customer_email, subject, plain_content, html_content, sender_type=SenderType.NOTIFY)

def send_support_contact_email(user_email: str, user_name: str, message_subject: str, message_body: str):
    """Email notification for support inquiries."""
    subject = f"Support Inquiry: {message_subject}"
    
    content = f"""
        <p>Hello <strong>{user_name}</strong>,</p>
        <p>We've received your inquiry regarding <strong>"{message_subject}"</strong>. Our support operatives are analyzing your request.</p>
        
        <div style="background-color: #05060a; border: 1px solid #1f2937; border-radius: 16px; padding: 25px; margin: 30px 0; text-align: left; background-image: radial-gradient(circle at top right, rgba(220, 38, 38, 0.05), transparent);">
            <p style="color: #6b7280; font-size: 10px; font-weight: 900; text-transform: uppercase; margin: 0 0 10px 0; letter-spacing: 1px;">Your Message Reference</p>
            <p style="color: #ffffff; font-size: 14px; margin: 0; line-height: 1.6; font-style: italic;">"{message_body}"</p>
        </div>
        
        <p style="color: #4b5563; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">Ticket ID: SUP-{os.urandom(4).hex().upper()}</p>
    """
    
    html_content = get_base_html(
        title="Support Ticket",
        preheader=f"Confirmed: {message_subject}",
        content_html=content
    )
    
    plain_content = f"""
    Hello {user_name},
    
    We have received your support inquiry: "{message_subject}".
    
    Message:
    {message_body}
    
    Our team will get back to you shortly.
    
    -- ServSync Support
    """
    
    return send_email(user_email, subject, plain_content, html_content, sender_type=SenderType.SUPPORT)

def send_admin_contact_notification(user_email: str, user_name: str, message_subject: str, message_body: str):
    """Notify the admin(s) of a new support inquiry."""
    primary_admin = os.getenv("ADMIN_EMAIL", DEFAULT_USER)
    secondary_admin = "servsyncnevermissaserviceagain@gmail.com"
    
    # Ensure unique recipients
    recipients = list(set([primary_admin, secondary_admin]))
    
    subject = f"NEW INQUIRY: {message_subject}"
    
    content = f"""
        <p>A new support inquiry has been successfully intercepted by the ServSync gateway.</p>
        <div style="background-color: #05060a; border: 1px solid #1f2937; border-radius: 16px; padding: 25px; margin: 30px 0; text-align: left;">
            <p style="color: #6b7280; font-size: 10px; font-weight: 900; text-transform: uppercase; margin: 0 0 5px 0; letter-spacing: 1px;">From</p>
            <p style="color: #ffffff; font-size: 14px; margin: 0 0 15px 0;"><strong>{user_name}</strong> ({user_email})</p>
            
            <p style="color: #6b7280; font-size: 10px; font-weight: 900; text-transform: uppercase; margin: 0 0 5px 0; letter-spacing: 1px;">Subject</p>
            <p style="color: #ffffff; font-size: 14px; margin: 0 0 15px 0;">{message_subject}</p>
            
            <p style="color: #6b7280; font-size: 10px; font-weight: 900; text-transform: uppercase; margin: 0 0 5px 0; letter-spacing: 1px;">Message Payload</p>
            <p style="color: #9ca3af; font-size: 13px; line-height: 1.6; font-style: italic;">"{message_body}"</p>
        </div>
        <p>The operative is awaiting a response. Proceed to the Admin Terminal to resolve.</p>
    """
    
    html_content = get_base_html(
        title="Admin Alert",
        preheader=f"New query from {user_name}",
        content_html=content,
        button_text="Open Admin Terminal",
        button_url="http://localhost:5173/admin-portal"
    )
    
    resolution_link = "http://localhost:5173/admin-portal"
    
    plain_content = f"""
    NEW INQUIRY RECEIVED
    
    From: {user_name} ({user_email})
    Subject: {message_subject}
    Message: {message_body}
    
    Resolution link: {resolution_link}
    """
    
    # Send to all admin recipients
    for recipient in recipients:
        send_email(recipient, subject, plain_content, html_content, sender_type=SenderType.SUPPORT)
    
    return True

def send_admin_reply_email(user_email: str, user_name: str, original_subject: str, reply_message: str):
    """Dispatch an admin response to a user's inquiry."""
    subject = f"RE: {original_subject} - Protocol Update"
    
    content = f"""
        <p>Hello <strong>{user_name}</strong>,</p>
        <p>The ServSync Administration has issued a response regarding your inquiry: <strong>"{original_subject}"</strong>.</p>
        
        <div style="background-color: #05060a; border: 1px solid #dc2626; border-radius: 16px; padding: 30px; margin: 30px 0; text-align: left; border-left: 5px solid #dc2626;">
            <p style="color: #dc2626; font-size: 10px; font-weight: 900; text-transform: uppercase; margin: 0 0 15px 0; letter-spacing: 2px;">Admin Response</p>
            <p style="color: #ffffff; font-size: 15px; margin: 0; line-height: 1.8;">{reply_message}</p>
        </div>
        
        <p style="color: #4b5563; font-size: 12px;">This communication has been dispatched from the secure admin gateway. Please contact us if further clarification is required.</p>
    """
    
    html_content = get_base_html(
        title="Official Response",
        preheader="Response from ServSync Support team.",
        content_html=content
    )
    
    plain_content = f"""
    Hello {user_name},
    
    The ServSync Administration has responded to your inquiry: "{original_subject}".
    
    Response:
    {reply_message}
    
    -- ServSync Administration
    """
    
    return send_email(user_email, subject, plain_content, html_content, sender_type=SenderType.SUPPORT)

def send_booking_confirmation_email(customer_email: str, customer_name: str, brand: str, model: str, service_type: str, scheduled_date: str):
    """Automated confirmation email sent immediately after booking creation."""
    subject = f"ServSync: Service Application Confirmed - {brand} {model}"
    
    content = f"""
        <p>Hello <strong>{customer_name}</strong>,</p>
        <p>Your service application for the <strong>{brand} {model}</strong> has been successfully received.</p>
        
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #05060a; border: 1px solid #1f2937; border-radius: 16px; margin: 30px 0;">
            <tr>
                <td style="padding: 20px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%">
                        <tr>
                            <td style="color: #6b7280; font-size: 11px; text-transform: uppercase; padding-bottom: 5px;">Service Type</td>
                            <td align="right" style="color: #ffffff; font-weight: 700;">{service_type}</td>
                        </tr>
                        <tr>
                            <td style="color: #6b7280; font-size: 11px; text-transform: uppercase; padding-bottom: 5px;">Scheduled Date</td>
                            <td align="right" style="color: #ffffff; font-weight: 700;">{scheduled_date}</td>
                        </tr>
                        <tr>
                            <td style="color: #6b7280; font-size: 11px; text-transform: uppercase;">Current Status</td>
                            <td align="right" style="color: #fbbf24; font-weight: 900; text-transform: uppercase;">Awaiting Review</td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        
        <p>Your vehicle has entered our secure processing queue. We will notify you once the application is confirmed.</p>
    """
    
    html_content = get_base_html(
        title="Application",
        preheader=f"Service application received for {brand} {model}.",
        content_html=content,
        button_text="Open Dashboard",
        button_url="http://localhost:5173/dashboard"
    )
    
    plain_content = f"""
    Hello {customer_name},
    
    Your service application for the {brand} {model} has been confirmed.
    
    Service Details:
    - Type: {service_type}
    - Date: {scheduled_date}
    - Current Status: Awaiting Review
    
    Track progress: http://localhost:5173/dashboard
    
    -- ServSync Notifications
    """
    
    return send_email(customer_email, subject, plain_content, html_content, sender_type=SenderType.NOTIFY)

def send_password_reset_email(user_email: str, user_name: str, reset_link: str):
    """Send a password reset email with a secure link."""
    subject = "ServSync: Password Reset Request"
    
    content = f"""
        <p>Hello <strong>{user_name}</strong>,</p>
        <p>We received a request to reset the password for your ServSync account. Click the button below to create a new password.</p>
        
        <div style="background-color: #05060a; border: 1px solid #d97706; border-radius: 16px; padding: 25px; margin: 30px 0; text-align: center;">
            <p style="color: #d97706; font-size: 10px; font-weight: 900; text-transform: uppercase; margin: 0 0 10px 0; letter-spacing: 2px;">⚠ Security Notice</p>
            <p style="color: #9ca3af; font-size: 13px; margin: 0;">This link expires in <strong style="color: #ffffff;">15 minutes</strong>. If you didn't request this reset, ignore this email.</p>
        </div>
    """
    
    html_content = get_base_html(
        title="Password Reset",
        preheader="Reset your ServSync password.",
        content_html=content,
        button_text="Reset My Password",
        button_url=reset_link
    )
    
    plain_content = f"""
    Hello {user_name},
    
    We received a request to reset your password.
    
    Click on this link to set a new password:
    {reset_link}
    
    This link expires in 15 minutes.
    
    If you didn't request this, please ignore this email.
    
    -- ServSync Security
    """
    
    return send_email(user_email, subject, plain_content, html_content, sender_type=SenderType.AUTH)
