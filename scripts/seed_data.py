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

        # Create demo activities with flexible assignment
        activities = [
            # Family-level activities (assigned_to_kid_id is None)
            Activity(
                title="Plan family vacation",
                description="Research destinations and book accommodations",
                user_id=demo_user.id,
                assigned_to_kid_id=None,  # Family activity
                done=False
            ),
            Activity(
                title="Family game night",
                description="Pick board games and prepare snacks",
                user_id=demo_user.id,
                assigned_to_kid_id=None,  # Family activity
                done=True
            ),
            Activity(
                title="Grocery shopping",
                description="Weekly grocery run",
                user_id=demo_user.id,
                assigned_to_kid_id=None,  # Family activity
                done=False
            ),
            Activity(
                title="Organize family photos",
                description="Sort and organize digital photos from this year",
                user_id=demo_user.id,
                assigned_to_kid_id=None,  # Family activity
                done=False
            ),

            # Ava's specific activities
            Activity(
                title="Read for 20 minutes",
                description="Continue reading chapter book",
                user_id=demo_user.id,
                assigned_to_kid_id=ava.id,  # Ava's activity
                done=False
            ),
            Activity(
                title="Practice addition facts",
                description="Work on math facts 1-12",
                user_id=demo_user.id,
                assigned_to_kid_id=ava.id,  # Ava's activity
                done=True
            ),
            Activity(
                title="Write in journal",
                description="Daily journal entry about today's activities",
                user_id=demo_user.id,
                assigned_to_kid_id=ava.id,  # Ava's activity
                done=False
            ),
            Activity(
                title="Science experiment",
                description="Volcano baking soda experiment",
                user_id=demo_user.id,
                assigned_to_kid_id=ava.id,  # Ava's activity
                done=False
            ),
            Activity(
                title="Piano practice",
                description="Practice scales and new song",
                user_id=demo_user.id,
                assigned_to_kid_id=ava.id,  # Ava's activity
                done=True
            ),

            # Ben's specific activities
            Activity(
                title="Nature observation",
                description="Observe and draw insects in the backyard",
                user_id=demo_user.id,
                assigned_to_kid_id=ben.id,  # Ben's activity
                done=True
            ),
            Activity(
                title="Count to 100",
                description="Practice counting by 1s, 5s, and 10s",
                user_id=demo_user.id,
                assigned_to_kid_id=ben.id,  # Ben's activity
                done=True
            ),
            Activity(
                title="Draw a picture",
                description="Free drawing time with colored pencils",
                user_id=demo_user.id,
                assigned_to_kid_id=ben.id,  # Ben's activity
                done=False
            ),
            Activity(
                title="Letter recognition",
                description="Practice identifying uppercase and lowercase letters",
                user_id=demo_user.id,
                assigned_to_kid_id=ben.id,  # Ben's activity
                done=False
            ),
            Activity(
                title="Story time",
                description="Listen to audiobook or read-aloud",
                user_id=demo_user.id,
                assigned_to_kid_id=ben.id,  # Ben's activity
                done=True
            ),
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


async def seed_additional_demo_data():
    """Add more diverse demo data for testing different scenarios."""
    db: Session = SessionLocal()
    try:
        # Get existing demo user
        demo_user = db.execute(
            select(User).where(User.email == "demo@homeschool.app")
        ).scalar_one_or_none()

        if not demo_user:
            print("❌ Demo user not found. Run basic seed first.")
            return

        # Get existing kids
        kids = db.execute(
            select(Kid).where(Kid.parent_id == demo_user.id)
        ).scalars().all()

        if len(kids) < 2:
            print("❌ Need at least 2 kids for additional demo data.")
            return

        ava, ben = kids[0], kids[1]

        # Add more varied activities with different properties
        additional_activities = [
            # More family activities
            Activity(
                title="Movie night preparation",
                description="Choose movie, make popcorn, set up blankets",
                user_id=demo_user.id,
                assigned_to_kid_id=None,
                done=False
            ),
            Activity(
                title="Spring cleaning",
                description="Declutter and organize common areas",
                user_id=demo_user.id,
                assigned_to_kid_id=None,
                done=False
            ),

            # More activities for Ava
            Activity(
                title="History research project",
                description="Research ancient Egypt for history unit",
                user_id=demo_user.id,
                assigned_to_kid_id=ava.id,
                done=False
            ),
            Activity(
                title="Creative writing",
                description="Write a short story about adventure",
                user_id=demo_user.id,
                assigned_to_kid_id=ava.id,
                done=False
            ),

            # More activities for Ben
            Activity(
                title="Building blocks challenge",
                description="Build a tower taller than yourself",
                user_id=demo_user.id,
                assigned_to_kid_id=ben.id,
                done=False
            ),
            Activity(
                title="Animal sounds game",
                description="Match animals to their sounds",
                user_id=demo_user.id,
                assigned_to_kid_id=ben.id,
                done=True
            ),
        ]

        db.add_all(additional_activities)
        db.commit()

        print("✅ Additional demo data added successfully!")
        print(f"Added {len(additional_activities)} more activities")

    except Exception as e:
        db.rollback()
        print(f"❌ Error adding additional demo data: {e}")
        raise
    finally:
        db.close()


def print_demo_data_summary():
    """Print a summary of the demo data for verification."""
    db: Session = SessionLocal()
    try:
        demo_user = db.execute(
            select(User).where(User.email == "demo@homeschool.app")
        ).scalar_one_or_none()

        if not demo_user:
            print("❌ No demo data found.")
            return

        kids = db.execute(
            select(Kid).where(Kid.parent_id == demo_user.id)
        ).scalars().all()

        activities = db.execute(
            select(Activity).where(Activity.user_id == demo_user.id)
        ).scalars().all()

        print(f"\n📊 Demo Data Summary:")
        print(f"User: {demo_user.email}")
        print(f"Kids: {len(kids)}")
        for kid in kids:
            kid_activities = [a for a in activities if a.assigned_to_kid_id == kid.id]
            completed = len([a for a in kid_activities if a.done])
            print(f"  - {kid.name}: {len(kid_activities)} activities ({completed} completed)")

        family_activities = [a for a in activities if a.assigned_to_kid_id is None]
        completed_family = len([a for a in family_activities if a.done])
        print(f"Family activities: {len(family_activities)} ({completed_family} completed)")
        print(f"Total activities: {len(activities)}")

    except Exception as e:
        print(f"❌ Error getting demo data summary: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import asyncio
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "additional":
            asyncio.run(seed_additional_demo_data())
        elif sys.argv[1] == "summary":
            print_demo_data_summary()
        else:
            print("Usage: python seed.py [additional|summary]")
    else:
        asyncio.run(seed_demo_data())