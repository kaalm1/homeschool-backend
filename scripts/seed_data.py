from sqlalchemy.orm import Session
from sqlalchemy import select

from svc.app.database import SessionLocal
from svc.app.models.user import User
from svc.app.models.kid import Kid
from svc.app.models.activity import Activity
from svc.app.utils.security import hash_password


async def seed_demo_data():
    """Seed the database with demo data."""
    db: Session = SessionLocal()
    try:
        # Check if demo user already exists
        existing_user = db.execute(
            select(User).where(User.email == "demo@homeschool.app")
        ).scalar_one_or_none()

        if existing_user:
            return  # Demo data already exists

        # Create demo user
        demo_user = User(
            email="demo@homeschool.app",
            password_hash=hash_password("demo123"),
            is_active=True
        )
        db.add(demo_user)
        db.flush()  # Get the user ID

        # Create demo kids
        ava = Kid(
            name="Ava",
            color="#fde68a",
            parent_id=demo_user.id
        )

        ben = Kid(
            name="Ben",
            color="#93c5fd",
            parent_id=demo_user.id
        )

        db.add_all([ava, ben])
        db.flush()  # Get the kid IDs

        # Create demo activities
        activities = [
            Activity(
                title="Read for 20 minutes",
                subject="Reading",
                kid_id=ava.id,
                done=False
            ),
            Activity(
                title="Practice addition facts",
                subject="Math",
                kid_id=ava.id,
                done=True
            ),
            Activity(
                title="Write in journal",
                subject="Writing",
                kid_id=ava.id,
                done=False
            ),
            Activity(
                title="Nature observation",
                subject="Science",
                kid_id=ben.id,
                done=True
            ),
            Activity(
                title="Count to 100",
                subject="Math",
                kid_id=ben.id,
                done=True
            ),
            Activity(
                title="Draw a picture",
                subject="Art",
                kid_id=ben.id,
                done=False
            ),
        ]

        db.add_all(activities)
        db.commit()

        print("✅ Demo data seeded successfully!")
        print("Demo login: demo@homeschool.app / demo123")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding demo data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(seed_demo_data())
