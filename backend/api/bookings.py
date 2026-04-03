from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List, Optional

# Modular relative imports
from database import get_db
import models, schemas
from auth import get_current_user 
from .email_service import send_booking_update_email, send_booking_confirmation_email
from .websocket_manager import manager

router = APIRouter(prefix="/bookings", tags=["Bookings"])

# 1. CREATE: Customer creates a booking with RC Upload and Logistics
@router.post("/create")
async def create_booking(
    # Vehicle & Service Info
    brand: str = Form(...),
    model: str = Form(...), 
    licensePlate: str = Form(...),
    serviceType: str = Form(...),
    date: str = Form(...),
    
    # Logistics
    pickupLocation: Optional[str] = Form(None),
    dropLocation: Optional[str] = Form(None),
    
    # File Upload
    rc_document: UploadFile = File(...),
    
    # Dependencies
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # RBAC Guard
    if current_user.role != models.UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Only customers can create bookings")

    # 1. FILE HANDLING: Reference path (Mocking upload for now)
    file_path = None
    if rc_document:
        file_path = f"uploads/rc_{licensePlate}_{rc_document.filename}"

    # 2. VEHICLE LOGIC: 
    vehicle = db.query(models.Vehicle).filter(
        models.Vehicle.license_plate == licensePlate,
        models.Vehicle.owner_id == current_user.id
    ).first()

    if not vehicle:
        vehicle = models.Vehicle(
            brand=brand,
            model=model,
            license_plate=licensePlate,
            owner_id=current_user.id,
            rc_url=file_path 
        )
        db.add(vehicle)
        db.flush() 

    # 3. SERVICE LOOKUP: Find service by name
    service = db.query(models.Service).filter(
        models.Service.name.ilike(f"%{serviceType}%")
    ).first()
    
    if not service:
        # Create a default service if it doesn't exist or return error
        # For this demo, let's assume services exist or create a dummy
        service = db.query(models.Service).first()
        if not service:
             raise HTTPException(status_code=400, detail=f"Service type '{serviceType}' not found.")

    # 4. Create the booking record
    try:
        # Handle 'YYYY-MM-DD' or ISO formats
        if len(date) == 10:
            scheduled_dt = datetime.strptime(date, "%Y-%m-%d")
        else:
            scheduled_dt = datetime.fromisoformat(date)
    except:
        scheduled_dt = datetime.utcnow()

    new_booking = models.Booking(
        vehicle_id=vehicle.id,
        customer_id=current_user.id,
        service_id=service.id,
        scheduled_at=scheduled_dt,
        pickup_location=pickupLocation,
        drop_location=dropLocation,
        status=models.BookingStatus.PENDING,
        total_amount=service.base_price
    )
    
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    
    # Automated Service Application Confirmation
    try:
        send_booking_confirmation_email(
            customer_email=current_user.email,
            customer_name=current_user.full_name,
            brand=brand,
            model=model,
            service_type=serviceType,
            scheduled_date=date
        )
    except Exception as e:
        print(f"Failed to dispatch booking confirmation: {e}")
    
    # Log the booking activity
    db.add(models.SystemLog(
        event_type="BOOKING",
        severity="INFO",
        description=f"New mission created: {brand} {model} for {current_user.email}",
        user_email=current_user.email,
        path="/bookings/create"
    ))
    db.commit()

    # Trigger Real-time Workshop Alert via WebSocket
    import asyncio
    asyncio.create_task(manager.broadcast_to_role("PROVIDER", {
        "type": "NEW_BOOKING_ALERT",
        "message": f"Critical: New Request for {brand} {model}",
        "timestamp": str(datetime.utcnow()),
        "booking_id": str(new_booking.id)
    }))
    
    return {
        "status": "success", 
        "booking_id": str(new_booking.id),
        "message": f"Service for {brand} {model} scheduled."
    }

# 2. READ: Get bookings (Customer sees their own, Admin/Provider sees all)
@router.get("/", response_model=List[schemas.BookingRead])
def get_bookings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role == models.UserRole.CUSTOMER:
        return db.query(models.Booking).filter(models.Booking.customer_id == current_user.id).all()
    return db.query(models.Booking).all()

# 3. UPDATE: Change booking status
@router.patch("/{booking_id}/status")
def update_booking_status(
    booking_id: UUID,
    req: schemas.BookingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role == models.UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Customers cannot update booking status")
        
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    old_status = booking.status.value
    booking.status = req.status
    
    # Handle fleet assignment
    if req.status == models.BookingStatus.ACCEPTED:
        if current_user.role == models.UserRole.PROVIDER:
            if not req.driver_id or not req.towing_van_id:
                raise HTTPException(status_code=400, detail="Must assign a driver and a towing van when accepting.")
        if req.driver_id:
            booking.driver_id = req.driver_id
        if req.towing_van_id:
            booking.towing_van_id = req.towing_van_id

    db.commit()
    
    # Automated notification trigger
    try:
        send_booking_update_email(
            customer_email=booking.customer.email,
            customer_name=booking.customer.full_name,
            booking_id=str(booking.id),
            old_status=old_status,
            new_status=req.status.value
        )
    except Exception as e:
        print(f"Failed to trigger status update email: {e}")

    # Log the status update
    db.add(models.SystemLog(
        event_type="BOOKING",
        severity="INFO",
        description=f"Mission status updated: {booking.id} ({old_status} -> {req.status.value}) by {current_user.role.value}",
        user_email=current_user.email,
        path=f"/bookings/{booking_id}/status"
    ))
    db.commit()

    # Trigger Real-time Customer Notification if Accepted
    if req.status == models.BookingStatus.ACCEPTED:
        import asyncio
        asyncio.create_task(manager.send_personal_message({
            "type": "BOOKING_ACCEPTED",
            "message": "Your service request has been accepted by a technician.",
            "booking_id": str(booking.id),
            "status": "ACCEPTED"
        }, str(booking.customer_id)))

    return {"status": "success", "message": f"Booking {booking_id} updated to {req.status}"}
