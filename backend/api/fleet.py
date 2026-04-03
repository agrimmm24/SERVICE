from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from database import get_db
import models, schemas
from auth import get_current_user

router = APIRouter(prefix="/fleet", tags=["Fleet Management"])

# --- Towing Vans ---

@router.post("/vans", response_model=schemas.TowingVanRead)
def create_van(
    req: schemas.TowingVanCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != models.UserRole.PROVIDER:
        raise HTTPException(status_code=403, detail="Only providers can manage fleet")
        
    van = models.TowingVan(
        provider_id=current_user.id,
        license_plate=req.license_plate,
        model_name=req.model_name,
        status=req.status
    )
    db.add(van)
    db.commit()
    db.refresh(van)
    return van

@router.get("/vans", response_model=List[schemas.TowingVanRead])
def get_vans(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role == models.UserRole.ADMIN:
        return db.query(models.TowingVan).all()
    if current_user.role == models.UserRole.PROVIDER:
        return db.query(models.TowingVan).filter(models.TowingVan.provider_id == current_user.id).all()
    raise HTTPException(status_code=403, detail="Access denied")

# --- Drivers ---

@router.post("/drivers", response_model=schemas.DriverRead)
def create_driver(
    req: schemas.DriverCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != models.UserRole.PROVIDER:
        raise HTTPException(status_code=403, detail="Only providers can manage fleet")
        
    driver = models.Driver(
        provider_id=current_user.id,
        full_name=req.full_name,
        phone_number=req.phone_number,
        license_number=req.license_number,
        status=req.status
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver

@router.get("/drivers", response_model=List[schemas.DriverRead])
def get_drivers(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role == models.UserRole.ADMIN:
        return db.query(models.Driver).all()
    if current_user.role == models.UserRole.PROVIDER:
        return db.query(models.Driver).filter(models.Driver.provider_id == current_user.id).all()
    raise HTTPException(status_code=403, detail="Access denied")
