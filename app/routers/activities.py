from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

from app.models.base import SessionLocal
from app.models.activity import Activity
from app.models.kid import Kid
from app.security import get_current_user

router = APIRouter()

# -------------------
# Pydantic Schemas
# -------------------

class ActivityCreate(BaseModel):
    title: str
    subject: str
    kid_id: int

class ActivityUpdate(BaseModel):
    title: str | None = None
    subject: str | None = None
    done: bool | None = None

class ActivityOut(BaseModel):
    id: int
    title: str
    subject: str
    done: bool
    kid_id: int

    class Config:
        from_attributes = True

# -------------------
# DB dependency
# -------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------
# Routes
# -------------------

@router.get("", response_model=List[ActivityOut])
def list_activities(user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    List all activities for all kids of the current parent
    """
    activities = db.query(Activity).join(Kid).filter(Kid.parent_id == user.id).all()
    return activities

@router.post("", response_model=ActivityOut)
def create_activity(data: ActivityCreate, user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Create a new activity for a kid
    """
    kid = db.query(Kid).filter(Kid.id == data.kid_id, Kid.parent_id == user.id).first()
    if not kid:
        raise HTTPException(status_code=404, detail="Kid not found")

    activity = Activity(title=data.title, subject=data.subject, kid_id=kid.id)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity

@router.patch("/{activity_id}", response_model=ActivityOut)
def update_activity(activity_id: int, data: ActivityUpdate, user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Update an activity (title, subject, done)
    """
    activity = db.query(Activity).join(Kid).filter(Activity.id == activity_id, Kid.parent_id == user.id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    if data.title is not None:
        activity.title = data.title
    if data.subject is not None:
        activity.subject = data.subject
    if data.done is not None:
        activity.done = data.done

    db.commit()
    db.refresh(activity)
    return activity

@router.delete("/{activity_id}", response_model=dict)
def delete_activity(activity_id: int, user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Delete an activity
    """
    activity = db.query(Activity).join(Kid).filter(Activity.id == activity_id, Kid.parent_id == user.id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    db.delete(activity)
    db.commit()
    return {"detail": "Activity deleted"}
