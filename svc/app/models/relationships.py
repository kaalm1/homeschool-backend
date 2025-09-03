# models/relationships.py
from sqlalchemy.orm import relationship

from svc.app.models.activity import Activity
from svc.app.models.user import User

Activity.week_assignments = relationship(
    "WeekActivity", back_populates="activity", cascade="all, delete-orphan"
)

User.week_activities = relationship(
    "WeekActivity", back_populates="user", cascade="all, delete-orphan"
)
