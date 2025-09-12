from typing import List

from svc.app.dal.activity_suggestion_repository import ActivitySuggestionRepository
from svc.app.dal.user_behavior_analytic_repository import (
    UserBehaviorAnalyticsRepository,
)
from svc.app.models.activity_suggestion import ActivitySuggestion
from svc.app.models.user_behavior_analytic import UserBehaviorAnalytic


class BehaviorAnalyticsService:
    def __init__(
        self,
        analytics_repo: UserBehaviorAnalyticsRepository,
        suggestion_repo: ActivitySuggestionRepository,
    ):
        self.analytics_repo = analytics_repo
        self.suggestion_repo = suggestion_repo

    def calculate_user_behavior_patterns(self, user_id: int) -> UserBehaviorAnalytic:
        """Calculate behavioral patterns for a user."""
        suggestions = self.suggestion_repo.get_user_suggestions(
            user_id, lookback_weeks=16
        )

        if len(suggestions) < 5:
            # Not enough data - return defaults
            return self.analytics_repo.create_or_update(
                user_id,
                {"sample_size": len(suggestions), "calculation_confidence": 0.1},
            )

        # Calculate marking patterns
        marked_count = sum(1 for s in suggestions if s.completion_status == "completed")
        marking_rate = marked_count / len(suggestions)

        # Analyze big vs small activities
        big_suggestions = [s for s in suggestions if self._is_big_activity(s.activity)]
        small_suggestions = [
            s for s in suggestions if not self._is_big_activity(s.activity)
        ]

        big_marking_rate = (
            sum(1 for s in big_suggestions if s.completion_status == "completed")
            / len(big_suggestions)
            if big_suggestions
            else 0
        )
        small_marking_rate = (
            sum(1 for s in small_suggestions if s.completion_status == "completed")
            / len(small_suggestions)
            if small_suggestions
            else 0
        )

        # Calculate success patterns
        successful_themes = self._calculate_theme_success_rates(suggestions)
        successful_activity_types = self._calculate_activity_type_success_rates(
            suggestions
        )
        successful_cost_ranges = self._calculate_cost_success_rates(suggestions)

        analytics_data = {
            "marking_rate": marking_rate,
            "marks_big_activities_only": big_marking_rate > 0.2
            and small_marking_rate < 0.1,
            "big_activity_marking_rate": big_marking_rate,
            "small_activity_marking_rate": small_marking_rate,
            "successful_themes": successful_themes,
            "successful_activity_types": successful_activity_types,
            "successful_cost_ranges": successful_cost_ranges,
            "sample_size": len(suggestions),
            "calculation_confidence": min(
                1.0, len(suggestions) / 50.0
            ),  # Full confidence at 50+ activities
        }

        return self.analytics_repo.create_or_update(user_id, analytics_data)

    def _is_big_activity(self, activity) -> bool:
        """Determine if activity is 'big' (expensive/special)."""
        if not activity:
            return False

        big_indicators = [
            any(cost in ["HIGH", "MEDIUM"] for cost in activity.costs or []),
            any(
                duration in ["HALF_DAY", "FULL_DAY"]
                for duration in activity.durations or []
            ),
            any(
                loc in ["MUSEUM", "ZOO", "AMUSEMENT_PARK"]
                for loc in activity.locations or []
            ),
            any(
                keyword in activity.title.lower()
                for keyword in ["museum", "zoo", "concert", "show"]
            ),
        ]
        return sum(big_indicators) >= 2

    def _calculate_theme_success_rates(
        self, suggestions: List[ActivitySuggestion]
    ) -> dict:
        theme_stats = {}
        for suggestion in suggestions:
            if not suggestion.activity or not suggestion.activity.themes:
                continue

            is_successful = suggestion.completion_status in [
                "completed",
                "likely_completed",
            ]

            for theme in suggestion.activity.themes:
                if theme not in theme_stats:
                    theme_stats[theme] = {"total": 0, "successful": 0}
                theme_stats[theme]["total"] += 1
                if is_successful:
                    theme_stats[theme]["successful"] += 1

        return {
            theme: stats["successful"] / stats["total"]
            for theme, stats in theme_stats.items()
            if stats["total"] >= 3  # Only include themes with 3+ examples
        }

    def _calculate_activity_type_success_rates(
        self, suggestions: List[ActivitySuggestion]
    ) -> dict:
        # Similar to themes but for activity types
        type_stats = {}
        for suggestion in suggestions:
            if not suggestion.activity or not suggestion.activity.activity_types:
                continue

            is_successful = suggestion.completion_status in [
                "completed",
                "likely_completed",
            ]

            for activity_type in suggestion.activity.activity_types:
                if activity_type not in type_stats:
                    type_stats[activity_type] = {"total": 0, "successful": 0}
                type_stats[activity_type]["total"] += 1
                if is_successful:
                    type_stats[activity_type]["successful"] += 1

        return {
            atype: stats["successful"] / stats["total"]
            for atype, stats in type_stats.items()
            if stats["total"] >= 3
        }

    def _calculate_cost_success_rates(
        self, suggestions: List[ActivitySuggestion]
    ) -> dict:
        cost_stats = {}
        for suggestion in suggestions:
            if not suggestion.activity or not suggestion.activity.costs:
                continue

            is_successful = suggestion.completion_status in [
                "completed",
                "likely_completed",
            ]

            for cost in suggestion.activity.costs:
                if cost not in cost_stats:
                    cost_stats[cost] = {"total": 0, "successful": 0}
                cost_stats[cost]["total"] += 1
                if is_successful:
                    cost_stats[cost]["successful"] += 1

        return {
            cost: stats["successful"] / stats["total"]
            for cost, stats in cost_stats.items()
            if stats["total"] >= 2  # Lower threshold for cost ranges
        }
