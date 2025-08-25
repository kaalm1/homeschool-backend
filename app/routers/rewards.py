
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from pydantic import BaseModel
from app.models.activity import Activity
from app.models.kid import Kid
from ..security import get_current_user, get_db

router = APIRouter()

class RewardSummary(BaseModel):
    kid_id: int
    kid_name: str
    stars: int

@router.get("/summary", response_model=list[RewardSummary])
def reward_summary(user=Depends(get_current_user), db: Session = Depends(get_db)):
    # Simple: stars = number of done activities
    kids = db.execute(select(Kid).where(Kid.parent_id==user.id)).scalars().all()
    res: list[RewardSummary] = []
    for k in kids:
        count = db.execute(select(func.count()).select_from(Activity).where(Activity.kid_id==k.id, Activity.done==True)).scalar() or 0
        res.append(RewardSummary(kid_id=k.id, kid_name=k.name, stars=int(count)))
    return res
