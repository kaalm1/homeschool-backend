from sqlalchemy.orm import Session
from sqlalchemy import select

from svc.app.database import SessionLocal
from svc.app.models.user import User
from svc.app.models.kid import Kid
from svc.app.models.activity import Activity
from svc.app.utils.security import hash_password
from svc.app.data.seed import GENERIC_FAMILY_ACTIVITIES


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

        # Create demo activities with flexible assignment
        activities = [
            Activity(
                title=a.title,
                description=a.description,
                done=a.done,
                assigned_to_kid_id=a.assigned_to_kid_id,
                costs=a.costs,
                durations=a.durations,
                participants=a.participants,
                locations=a.locations,
                seasons=a.seasons,
                age_groups=a.age_groups,
                frequency=a.frequency,
                themes=a.themes,
                activity_types=a.activity_types,
                user_id=demo_user.id  # override here
            )
            for a in GENERIC_FAMILY_ACTIVITIES
        ]

        db.add_all(activities)
        db.commit()

        print("✅ Demo data seeded successfully!")
        print("Demo login: demo@homeschool.app / demo123")
        print(f"Created {len(activities)} activities:")

        # Print summary of created activities
        family_activities = [a for a in activities if a.assigned_to_kid_id is None]
        ava_activities = [a for a in activities if a.assigned_to_kid_id == ava.id]
        ben_activities = [a for a in activities if a.assigned_to_kid_id == ben.id]

        print(f"  - {len(family_activities)} family activities")
        print(f"  - {len(ava_activities)} activities for Ava")
        print(f"  - {len(ben_activities)} activities for Ben")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding demo data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(seed_demo_data())