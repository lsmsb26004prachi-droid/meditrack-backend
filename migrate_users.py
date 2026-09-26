from database import engine
from sqlalchemy import text

def run_migration():
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN date_of_birth DATE;"))
            conn.execute(text("ALTER TABLE users ADD COLUMN sex VARCHAR(20);"))
            conn.execute(text("ALTER TABLE users ADD COLUMN height_cm FLOAT;"))
            conn.execute(text("ALTER TABLE users ADD COLUMN weight_kg FLOAT;"))
        print("Success! Added profile columns to the users table.")
    except Exception as e:
        print(f"Error (or columns already exist): {e}")

if __name__ == "__main__":
    run_migration()