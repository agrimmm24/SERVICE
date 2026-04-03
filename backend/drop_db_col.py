import sqlalchemy as sa
from database import engine

try:
    with engine.begin() as con:
        con.execute(sa.text("ALTER TABLE users DROP COLUMN IF EXISTS created_at"))
        print("Successfully dropped created_at from users table")
except Exception as e:
    print(f"Error dropping column: {e}")
