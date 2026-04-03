import sqlalchemy as sa
from database import engine

def main():
    try:
        with engine.begin() as con: # Note: using begin() for automatic commit in SQLAlchemy 2.0
            con.execute(sa.text("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
            print("Successfully added created_at to users table")
    except Exception as e:
        print(f"Error (maybe column already exists): {e}")

if __name__ == "__main__":
    main()
