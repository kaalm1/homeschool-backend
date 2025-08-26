from passlib.hash import bcrypt
from sqlalchemy import select

from svc.app.models.activity import Activity
from svc.app.models.base import SessionLocal
from svc.app.models.kid import Kid
from svc.app.models.user import User


def seed_demo():
    db = SessionLocal()
    try:
        if not db.execute(
            select(User).where(User.email == "demo@home.school")
        ).scalar_one_or_none():
            user = User(email="demo@home.school", password_hash=bcrypt.hash("demo123"))
            db.add(user)
            db.flush()
            kid1 = Kid(name="Ava", color="#fde68a", parent_id=user.id)
            kid2 = Kid(name="Ben", color="#93c5fd", parent_id=user.id)
            db.add_all([kid1, kid2])
            db.flush()
            db.add_all(
                [
                    Activity(
                        title="Read 10 minutes", subject="Reading", kid_id=kid1.id
                    ),
                    Activity(title="Count to 50", subject="Math", kid_id=kid1.id),
                    Activity(
                        title="Leaf hunt outside", subject="Science", kid_id=kid2.id
                    ),
                ]
            )
            db.commit()
    finally:
        db.close()
