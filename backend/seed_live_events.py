import sys
import os
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from database import SessionLocal, engine
import models
from security import hash_password

def seed_live():
    print("--- Seeding Live Events and Messages ---")
    db = SessionLocal()
    try:
        # Check if we already have seeded
        existing = db.query(models.LiveEvent).first()
        if existing:
            print("Live events already exist, skipping seeding.")
            return
            
        # Create some seed users
        sami = models.User(
            full_name="Sami Trabelsi",
            email="sami@newshub.com",
            password_hash=hash_password("Password123!"),
            role="user"
        )
        sarah = models.User(
            full_name="Sarah Benslimen",
            email="sarah@newshub.com",
            password_hash=hash_password("Password123!"),
            role="user"
        )
        editor_user = models.User(
            full_name="Alex Mercer (Editor)",
            email="alex@newshub.com",
            password_hash=hash_password("Password123!"),
            role="editor"
        )
        db.add_all([sami, sarah, editor_user])
        db.commit()
        db.refresh(sami)
        db.refresh(sarah)
        db.refresh(editor_user)
        print("Created seed users.")

        # Create active Live Event
        live_ev = models.LiveEvent(
            title="TechTalk: The Future of Web Development with Angular 19",
            description="Our senior editors dive deep into Angular's new reactive primitives, signal-based components, advanced SSR capabilities, and state management strategies in modern frontends.",
            category="technology",
            cover_image="https://images.unsplash.com/photo-1517694712202-14dd9538aa97",
            status="live",
            premium_only=False,
            editor_user_id=editor_user.id,
            started_at=datetime.utcnow()
        )
        
        # Create upcoming Live Event
        upcoming_ev = models.LiveEvent(
            title="Global Market Outlook: Navigating Economic Shifts in 2026",
            description="Leading financial analysts break down interest rates, emerging market trends, and inflation projections. Set your reminders for this exclusive Q&A panel.",
            category="business",
            cover_image="https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f",
            status="upcoming",
            premium_only=True,
            editor_user_id=editor_user.id
        )
        
        db.add_all([live_ev, upcoming_ev])
        db.commit()
        db.refresh(live_ev)
        db.refresh(upcoming_ev)
        print("Created live and upcoming events.")

        # Add live chat messages
        msg1 = models.LiveMessage(
            live_event_id=live_ev.id,
            user_id=sami.id,
            message_type="chat",
            content="The SSR performance in Angular 19 is absolutely incredible! Standard page loads are down to milliseconds 🚀"
        )
        msg2 = models.LiveMessage(
            live_event_id=live_ev.id,
            user_id=sarah.id,
            message_type="chat",
            content="Are signals fully replacing RxJS in this architectural demo, or are they coexisting?"
        )
        msg3 = models.LiveMessage(
            live_event_id=live_ev.id,
            user_id=sami.id,
            message_type="chat",
            content="They work beautifully together! Signals handle the synchronous component state, while RxJS manages complex async event streams and data pipes."
        )
        msg4 = models.LiveMessage(
            live_event_id=live_ev.id,
            user_id=editor_user.id,
            message_type="chat",
            content="Exactly Sami! We will be showcasing how to bridge Observables to Signals using `toSignal()` in just a few minutes."
        )
        msg5 = models.LiveMessage(
            live_event_id=live_ev.id,
            user_id=sarah.id,
            message_type="chat",
            content="That makes so much sense! Super excited for the code walk-through now."
        )
        
        db.add_all([msg1, msg2, msg3, msg4, msg5])
        db.commit()
        print("Seeded active live chat conversation.")

    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_live()
