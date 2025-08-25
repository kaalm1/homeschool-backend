
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from ..db import Kid
from ..security import get_current_user, get_db

router = APIRouter()

class KidOut(BaseModel):
    id: int
    name: str
    color: str
    class Config:
        from_attributes = True

@router.get("", response_model=list[KidOut])
def list_kids(user=Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(select(Kid).where(Kid.parent_id==user.id)).scalars().all()
    return rows
