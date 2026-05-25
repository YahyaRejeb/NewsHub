import sys
import os

# Ensure the script can find the other backend modules
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from database import (
    _ensure_database_exists, 
    SQLALCHEMY_DATABASE_URL, 
    ensure_schema_extensions, 
    engine
)
from models import Base

def init_db():
    print("--- NewsHub Database Initialization ---")
    
    # 1. Create the MySQL Database (the one you see in phpMyAdmin)
    print("1. Creating the database if it doesn't exist...")
    try:
        _ensure_database_exists(SQLALCHEMY_DATABASE_URL)
        print(f"   -> Success! Database is ready.")
    except Exception as e:
        print(f"   -> Error creating database: {e}")
        print("   Make sure your MySQL server (e.g. XAMPP/phpMyAdmin) is running.")
        return

    # 2. Create all tables based on the classes in models.py
    print("\n2. Creating all tables based on the models...")
    try:
        Base.metadata.create_all(bind=engine)
        print("   -> Success! All tables created (users, interests, news, live_events, etc.).")
    except Exception as e:
        print(f"   -> Error creating tables: {e}")
        return
    
    # 3. Run any schema extensions and seed the default interests
    print("\n3. Running schema extensions and seeding default data...")
    try:
        ensure_schema_extensions()
        print("   -> Success! Default interests seeded and extensions applied.")
    except Exception as e:
        print(f"   -> Error during schema extensions: {e}")
        return
    
    print("\n--- Initialization Complete! You can check phpMyAdmin now. ---")

if __name__ == "__main__":
    init_db()
