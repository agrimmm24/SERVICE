from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas

router = APIRouter(prefix="/services", tags=["Services"])

@router.get("/", response_model=List[schemas.ServiceRead])
def get_services(db: Session = Depends(get_db)):
    """Fetch all available service offerings."""
    return db.query(models.Service).all()
