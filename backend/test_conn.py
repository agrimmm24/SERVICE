from database import SessionLocal
import models

def test_conn():
    db = SessionLocal()
    try:
        print("Testing DB connection...")
        services = db.query(models.Service).all()
        print(f"Success! Found {len(services)} services.")
        for s in services:
            print(f"- {s.name} ({s.vehicle_type})")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Connection failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_conn()
