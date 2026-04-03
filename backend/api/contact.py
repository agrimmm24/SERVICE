from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from .email_service import send_support_contact_email, send_admin_contact_notification
from .rate_limiter import get_rate_limiter
from typing import Optional

router = APIRouter(prefix="/contact", tags=["Contact"])

@router.post("/submit", dependencies=[Depends(get_rate_limiter(limit=3, window_seconds=60))])
async def submit_contact_form(
    contact_in: schemas.ContactMessageCreate,
    db: Session = Depends(get_db)
):
    # 1. Persist to Database
    new_message = models.ContactMessage(
        name=contact_in.name,
        email=contact_in.email,
        subject=contact_in.subject,
        message=contact_in.message
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    # 2. Logic to notify support team (and user)
    try:
        # Confirmation to User
        send_support_contact_email(
            user_email=contact_in.email,
            user_name=contact_in.name,
            message_subject=contact_in.subject,
            message_body=contact_in.message
        )

        # Alert to Admin
        send_admin_contact_notification(
            user_email=contact_in.email,
            user_name=contact_in.name,
            message_subject=contact_in.subject,
            message_body=contact_in.message
        )
    except Exception as e:
        print(f"Notification Error: {e}")

    # 3. Log the support signal
    db.add(models.SystemLog(
        event_type="ACCESS",
        severity="INFO",
        description=f"New support signal received from {contact_in.email}: {contact_in.subject}",
        user_email=contact_in.email,
        path="/contact/submit"
    ))
    db.commit()

    return {
        "status": "success",
        "message": "Protocol accepted. Our support unit and administration have been notified.",
        "id": str(new_message.id)
    }
