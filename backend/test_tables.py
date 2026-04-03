from sqlalchemy import create_engine, text
from database import SQLALCHEMY_DATABASE_URL

def verify_tables():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        try:
            res1 = conn.execute(text("SELECT count(*) FROM drivers"))
            res2 = conn.execute(text("SELECT count(*) FROM towing_vans"))
            print(f"Drivers count: {res1.scalar()}")
            print(f"Vans count: {res2.scalar()}")
            
            # Create the tables manually just in case Base.metadata.create_all isn't triggereing
            from models import Base
            Base.metadata.create_all(bind=engine)
            print("Successfully ensured tables exist.")
        except Exception as e:
            print(f"Error checking tables: {e}")

if __name__ == "__main__":
    verify_tables()
