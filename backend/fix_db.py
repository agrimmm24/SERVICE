from sqlalchemy import text
from database import engine

def fix_db():
    print("Connecting to database to add missing columns...")
    try:
        with engine.connect() as connection:
            # Check if columns exist before adding (safeguard)
            try:
                connection.execute(text("ALTER TABLE system_logs ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45)"))
                connection.execute(text("ALTER TABLE system_logs ADD COLUMN IF NOT EXISTS method VARCHAR(10)"))
                connection.execute(text("ALTER TABLE system_logs ADD COLUMN IF NOT EXISTS path VARCHAR(255)"))
                connection.commit()
                print("✅ Successfully added missing columns to 'system_logs' table.")
            except Exception as e:
                print(f"Error during ALTER TABLE: {e}")
                connection.rollback()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    fix_db()
