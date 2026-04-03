from sqlalchemy import create_engine, text
from database import SQLALCHEMY_DATABASE_URL

def run_migration():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS towing_van_id UUID;"))
            conn.execute(text("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS driver_id UUID;"))
            
            # Add foreign keys if possible, but safe to just have them as UUID columns for now
            print("Successfully added towing_van_id and driver_id to bookings table.")
        except Exception as e:
            print(f"Migration error (might already exist): {e}")

if __name__ == "__main__":
    run_migration()
