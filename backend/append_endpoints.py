import os

main_py_path = r"c:\Users\Lenovo\Downloads\SERVICE\main\backend\main.py"
content_to_append = r"""
# --- GPS Tracking Endpoints ---
from uuid import UUID
from datetime import datetime

@app.post("/api/tracking/{booking_id}/update")
def update_driver_location(booking_id: UUID, req: schemas.DriverLocationUpdate, db: Session = Depends(get_db)):
    \"\"\"Update or create a driver's live location for an active booking.\"\"\"
    # Verify booking exists and is in ACCEPTED state
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    # In a real app, we would verify that the current_user is the provider for this booking
    
    if booking.status != models.BookingStatus.ACCEPTED:
        raise HTTPException(status_code=400, detail="Tracking only available for ACCEPTED bookings")

    location = db.query(models.DriverLocation).filter(models.DriverLocation.booking_id == booking_id).first()
    if location:
        location.latitude = req.latitude
        location.longitude = req.longitude
        location.updated_at = datetime.utcnow()
    else:
        location = models.DriverLocation(
            booking_id=booking_id,
            latitude=req.latitude,
            longitude=req.longitude
        )
        db.add(location)
    
    db.commit()
    return {"status": "success"}

@app.get("/api/tracking/{booking_id}/location", response_model=schemas.DriverLocationRead)
def get_driver_location(booking_id: UUID, db: Session = Depends(get_db)):
    \"\"\"Retrieve the current live location for a booking's driver.\"\"\"
    location = db.query(models.DriverLocation).filter(models.DriverLocation.booking_id == booking_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="No active tracking found for this booking")
    return location
"""

with open(main_py_path, "a", encoding="utf-8") as f:
    f.write(content_to_append)

print(f"Successfully appended tracking endpoints to {main_py_path}")
