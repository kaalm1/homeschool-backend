from sqlalchemy import Integer, String, Column, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    subject = Column(String, default="General")
    done = Column(Boolean, default=False)
    kid_id = Column(Integer, ForeignKey("kids.id"), nullable=False)

    kid = relationship("Kid", back_populates="activities")
