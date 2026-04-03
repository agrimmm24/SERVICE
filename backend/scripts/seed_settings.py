import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Add parent directory to path so we can import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import models

def seed_settings():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not found in .env")
        return

    engine = create_engine(db_url)
    session = Session(engine)

    # New settings to add
    new_settings = [
        {
            "key": "platform_fee_percentage",
            "value": "10.0",
            "description": "Service fee percentage applied to all bookings."
        },
        {
            "key": "max_vehicles_per_user",
            "value": "5",
            "description": "Maximum number of vehicles a customer can register."
        },
        {
            "key": "otp_expiry_minutes",
            "value": "5",
            "description": "Duration in minutes before an OTP expires."
        },
        {
            "key": "emergency_contact_number",
            "value": "+91 98765 43210",
            "description": "Primary emergency support number shown platform-wide."
        },
        {
            "key": "workshop_auto_approval",
            "value": "false",
            "description": "Automatically approve new workshop registrations."
        },
        {
            "key": "min_service_price",
            "value": "499.0",
            "description": "Global minimum base price for any service offering."
        },
        {
            "key": "registration_enabled",
            "value": "true",
            "description": "Enable or disable new user registration manually."
        },
        {
            "key": "tax_rate_percentage",
            "value": "18.0",
            "description": "The standard tax rate percentage applied to all invoices."
        },
        {
            "key": "session_timeout_minutes",
            "value": "60",
            "description": "The number of minutes after which a session will automatically expire."
        },
        {
            "key": "max_login_attempts",
            "value": "5",
            "description": "Maximum allowed failed login attempts before a lockout occurs."
        },
        {
            "key": "support_email",
            "value": "ops@servsync.com",
            "description": "The primary email address for all system-generated support notifications."
        },
        {
            "key": "seo_meta_title",
            "value": "ServSync - Premium Vehicle Services Redefined",
            "description": "The default SEO title for the main landing page."
        },
        {
            "key": "seo_meta_description",
            "value": "The first decentralized premium vehicle servicing ecosystem. Secure, transparent, and ultra-reliable.",
            "description": "The default meta description for search engines."
        }
    ]

    print("--- Seeding System Settings ---")
    for s_data in new_settings:
        existing = session.query(models.SystemSettings).filter(models.SystemSettings.key == s_data["key"]).first()
        if not existing:
            new_s = models.SystemSettings(
                key=s_data["key"],
                value=s_data["value"],
                description=s_data["description"]
            )
            session.add(new_s)
            print(f"Added: {s_data['key']} = {s_data['value']}")
        else:
            print(f"Skipping (exists): {s_data['key']}")

    session.commit()
    print("--- Seeding Complete ---")
    session.close()

if __name__ == "__main__":
    seed_settings()
