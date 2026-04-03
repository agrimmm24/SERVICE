from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models, schemas
from auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=List[schemas.UserRead])
def get_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Fetch all users. Restricted to ADMIN users."""
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can manage users")
    
    return db.query(models.User).all()
