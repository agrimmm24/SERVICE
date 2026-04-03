from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models, auth

def seed_data():
    # Recreate tables to apply schema changes
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Clear existing data to avoid primary key conflicts (Optional)
        # db.query(models.User).delete()
        
        # 1. Create Services for 2-Wheelers
        bike_services = [
            models.Service(name="Bike Oil Change", vehicle_type=models.VehicleType.TWO_WHEELER, base_price=25.00, estimated_time_mins=30),
            models.Service(name="Chain Lubrication", vehicle_type=models.VehicleType.TWO_WHEELER, base_price=15.00, estimated_time_mins=20),
            models.Service(name="Full Bike Service", vehicle_type=models.VehicleType.TWO_WHEELER, base_price=80.00, estimated_time_mins=300),
            models.Service(name="Clutch plates", vehicle_type=models.VehicleType.TWO_WHEELER, base_price=20.00, estimated_time_mins=90)
        ]

        # 2. Create Services for 4-Wheelers
        car_services = [
            models.Service(name="Car Oil Change", vehicle_type=models.VehicleType.FOUR_WHEELER, base_price=60.00, estimated_time_mins=45),
            models.Service(name="Brake Pad Replacement", vehicle_type=models.VehicleType.FOUR_WHEELER, base_price=120.00, estimated_time_mins=90),
            models.Service(name="Car Deep Cleaning", vehicle_type=models.VehicleType.FOUR_WHEELER, base_price=50.00, estimated_time_mins=120),
            models.Service(name="Full Car Service", vehicle_type=models.VehicleType.FOUR_WHEELER, base_price=150.00, estimated_time_mins=500),
            models.Service(name="Car Lubrication", vehicle_type=models.VehicleType.FOUR_WHEELER, base_price=200.00, estimated_time_mins=90),
        ]

        # 3. Create Test Users
        raw_users = [
            {"email": "sri.agrimsri@gmail.com", "phone": "7880692270", "name": "Master Admin", "role": models.UserRole.ADMIN, "pw": "admin123"},
            {"email": "servsyncnevermissaserviceagain@gmail.com", "phone": "0000000001", "name": "System Admin", "role": models.UserRole.ADMIN, "pw": "admin123"},
            {"email": "mechanic@garage.com", "phone": "9988776655", "name": "Quick Fix Garage", "role": models.UserRole.PROVIDER, "pw": "provider123"},
            {"email": "bhumisharma2786@gmail.com", "phone": "8877665544", "name": "Bhoomi Sharma", "role": models.UserRole.CUSTOMER, "pw": "customer123"},
        ]

        # Helper function for idempotent seeding
        def seed_service(service_data):
            existing = db.query(models.Service).filter(
                models.Service.name == service_data.name,
                models.Service.vehicle_type == service_data.vehicle_type
            ).first()
            if existing:
                existing.base_price = service_data.base_price
                existing.estimated_time_mins = service_data.estimated_time_mins
            else:
                db.add(service_data)

        for s in bike_services: seed_service(s)
        for s in car_services: seed_service(s)
        
        for u in raw_users:
            exists = db.query(models.User).filter(models.User.email == u["email"]).first()
            if not exists:
                db.add(models.User(
                    email=u["email"],
                    phone_number=u["phone"],
                    full_name=u["name"],
                    role=u["role"],
                    password_hash=auth.get_password_hash(u["pw"]),
                    is_verified=True
                ))

        db.commit()
        print("OK: Database successfully synced with seed data!")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()