import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from database import SessionLocal
import models

def make_all_premium():
    db = SessionLocal()
    try:
        users = db.query(models.User).all()
        for user in users:
            user.is_premium = True
            print(f"User {user.email} is now premium.")
        db.commit()
        print("Successfully made all seeded users premium.")
    except Exception as e:
        print(f"Error updating users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    make_all_premium()
