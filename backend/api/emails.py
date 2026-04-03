from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from .email_service import send_email, get_base_html

router = APIRouter(prefix="/emails", tags=["Emails"])

class EmailSend(BaseModel):
    to_email: EmailStr
    subject: str
    body: str
    is_html: Optional[bool] = False

@router.post("/send")
def trigger_email(email_in: EmailSend):
    """Manually send an email from the domain (Admin feature)."""
    # In a real app, we'd add admin dependency check here
    # If it's HTML, we wrap it in our premium template
    final_html = None
    if email_in.is_html:
        final_html = get_base_html(
            title=email_in.subject,
            preheader="Platform communication from ServSync.",
            content_html=f"<p>{email_in.body.replace('\n', '<br>')}</p>"
        )

    success = send_email(
        to_email=email_in.to_email,
        subject=email_in.subject,
        body=email_in.body,
        html_body=final_html
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email via SMTP service")
    
    return {"status": "success", "message": "Email dispatched successfully"}
