
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Integer, String, Boolean, ForeignKey, Column
from sqlalchemy.orm import relationship

from .settings import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    kids = relationship("Kid", back_populates="parent")

class Kid(Base):
    __tablename__ = "kids"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    color = Column(String, default="#a7f3d0")
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    parent = relationship("User", back_populates="kids")
    activities = relationship("Activity", back_populates="kid")

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    subject = Column(String, default="General")
    done = Column(Boolean, default=False)
    kid_id = Column(Integer, ForeignKey("kids.id"), nullable=False)

    kid = relationship("Kid", back_populates="activities")

def seed_demo():
    # seed one demo user with two kids and a couple of activities
    from passlib.hash import bcrypt
    db = SessionLocal()
    try:
        from sqlalchemy import select
        if not db.execute(select(User).where(User.email == "demo@home.school")).scalar_one_or_none():
            user = User(email="demo@home.school", password_hash=bcrypt.hash("demo123"))
            db.add(user); db.flush()
            kid1 = Kid(name="Ava", color="#fde68a", parent_id=user.id)
            kid2 = Kid(name="Ben", color="#93c5fd", parent_id=user.id)
            db.add_all([kid1, kid2]); db.flush()
            db.add_all([
                Activity(title="Read 10 minutes", subject="Reading", kid_id=kid1.id),
                Activity(title="Count to 50", subject="Math", kid_id=kid1.id),
                Activity(title="Leaf hunt outside", subject="Science", kid_id=kid2.id),
            ])
            db.commit()
    finally:
        db.close()
