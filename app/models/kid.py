from sqlalchemy import Integer, String, Column, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class Kid(Base):
    __tablename__ = "kids"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    color = Column(String, default="#a7f3d0")
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    parent = relationship("User", back_populates="kids")
    activities = relationship("Activity", back_populates="kid")
