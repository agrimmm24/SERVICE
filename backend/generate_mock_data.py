import os
import sys

# Ensure this relies on the backend path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
import models
import auth
from datetime import datetime, timedelta
import random

def generate_mock_data():
    db = SessionLocal()
    try:
        print("Injecting rich mock data to repair vanished visualizations...")
        
        # Ensure we have roles
        provider = db.query(models.User).filter(models.User.role == models.UserRole.PROVIDER).first()
        customer = db.query(models.User).filter(models.User.role == models.UserRole.CUSTOMER).first()

        if not provider or not customer:
            print("Err: Core testing users missing. Did you run 'python seed.py'?")
            return

        # 1. Create a few Extra Users
        if db.query(models.User).count() < 10:
            extra_users = [
                models.User(email=f"operative{i}@servsync.com", phone_number=f"5550000{i}", full_name=f"Operative Alpha {i}", role=models.UserRole.CUSTOMER, password_hash=auth.get_password_hash("test1234"), created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60)))
                for i in range(1, 6)
            ]
            db.add_all(extra_users)
            db.commit()

        # Get Services to hook up
        bike_service = db.query(models.Service).filter(models.Service.vehicle_type == models.VehicleType.TWO_WHEELER).first()
        car_service = db.query(models.Service).filter(models.Service.vehicle_type == models.VehicleType.FOUR_WHEELER).first()
        
        if not bike_service or not car_service:
            print("Services missing. Please run 'python seed.py' first.")
            return

        # 2. Add Vehicles 
        if db.query(models.Vehicle).count() == 0:
            vehicles = [
                models.Vehicle(owner_id=customer.id, type=models.VehicleType.TWO_WHEELER, brand="Yamaha", model="R15", license_plate="SYN-1100"),
                models.Vehicle(owner_id=customer.id, type=models.VehicleType.FOUR_WHEELER, brand="Honda", model="Civic", license_plate="SYN-4455")
            ]
            db.add_all(vehicles)
            db.commit()

        # Get vehicles
        bike = db.query(models.Vehicle).filter(models.Vehicle.type == models.VehicleType.TWO_WHEELER).first()
        car = db.query(models.Vehicle).filter(models.Vehicle.type == models.VehicleType.FOUR_WHEELER).first()

        # 3. Add Bookings intelligently distributed over the last 60 days
        if db.query(models.Booking).count() < 20:
            print("Generating historical booking data...")
            bookings = []
            now = datetime.utcnow()
            for _ in range(35):  # Create 35 randomized bookings
                days_ago = random.randint(1, 58) 
                is_bike = random.choice([True, False])
                target_date = now - timedelta(days=days_ago) # historical date
                
                b = models.Booking(
                    customer_id=customer.id,
                    provider_id=provider.id,
                    vehicle_id=bike.id if is_bike else car.id,
                    service_id=bike_service.id if is_bike else car_service.id,
                    status=random.choice([models.BookingStatus.COMPLETED, models.BookingStatus.ACCEPTED, models.BookingStatus.PENDING]),
                    scheduled_at=target_date + timedelta(days=1),
                    total_amount=round(random.uniform(50.0, 300.0), 2),
                    created_at=target_date
                )
                bookings.append(b)
            db.add_all(bookings)
            db.commit()

        # 4. Add Contact Queries
        if db.query(models.ContactMessage).count() == 0:
            queries = [
                models.ContactMessage(name="John Doe", email="john@example.com", subject="Urgent Engine Issue", message="Can you prioritize my vehicle?", status=models.ContactMessageStatus.PENDING),
                models.ContactMessage(name="Jane Smith", email="jane@example.com", subject="Billing Question", message="I noticed an anomaly in my receipt.", status=models.ContactMessageStatus.RESOLVED, admin_reply="Refund issued.", replied_at=datetime.utcnow() - timedelta(minutes=60))
            ]
            db.add_all(queries)
            db.commit()
            
        print("Data Architecture repaired successfully! Refresh your Admin Dashboard visualizations.")

    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    generate_mock_data()
