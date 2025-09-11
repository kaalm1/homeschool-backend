from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from svc.app.dal.base_repository import BaseRepository
from svc.app.models.user_behavior_analytic import UserBehaviorAnalytic


class UserBehaviorAnalyticsRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, UserBehaviorAnalytic)

    def get_by_user(self, user_id: int) -> Optional[UserBehaviorAnalytic]:
        return (
            self.db.query(UserBehaviorAnalytic)
            .filter(UserBehaviorAnalytic.user_id == user_id)
            .first()
        )

    def create_or_update(
        self, user_id: int, analytics_data: dict
    ) -> UserBehaviorAnalytic:
        analytics = self.get_by_user(user_id)
        if analytics:
            for key, value in analytics_data.items():
                if hasattr(analytics, key):
                    setattr(analytics, key, value)
            analytics.last_calculated = datetime.utcnow()
        else:
            analytics = UserBehaviorAnalytic(user_id=user_id, **analytics_data)
            self.db.add(analytics)

        self.db.commit()
        return analytics
