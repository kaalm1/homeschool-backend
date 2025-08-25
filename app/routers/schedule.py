
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from app.models.activity import Activity
from app.models.kid import Kid
from ..security import get_current_user, get_db

router = APIRouter()

class ActivityOut(BaseModel):
    id: int
    title: str
    subject: str
    kid_id: int
    done: bool
    class Config:
        from_attributes = True

class ActivityIn(BaseModel):
    title: str
    subject: str = "General"
    kid_id: int

@router.get("/today", response_model=list[ActivityOut])
def today(user=Depends(get_current_user), db: Session = Depends(get_db)):
    # MVP: return all activities for the user's kids (no date dimension yet)
    kid_ids = [k.id for k in db.execute(select(Kid).where(Kid.parent_id==user.id)).scalars().all()]
    rows = db.execute(select(Activity).where(Activity.kid_id.in_(kid_ids))).scalars().all()
    return rows

@router.post("/add", response_model=ActivityOut)
def add_activity(data: ActivityIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    kid = db.get(Kid, data.kid_id)
    if not kid or kid.parent_id != user.id:
        raise HTTPException(status_code=404, detail="Kid not found")
    a = Activity(title=data.title, subject=data.subject, kid_id=data.kid_id)
    db.add(a); db.commit(); db.refresh(a)
    return a

class ToggleIn(BaseModel):
    id: int

@router.post("/toggle", response_model=ActivityOut)
def toggle(data: ToggleIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.get(Activity, data.id)
    if not a:
        raise HTTPException(status_code=404, detail="Activity not found")
    # security: ensure activity belongs to current user
    if a.kid.parent_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    a.done = not a.done
    db.add(a); db.commit(); db.refresh(a)
    return a
