from datetime import date, datetime
from typing import List, Optional

from svc.app.dal.activity_suggestion_repository import ActivitySuggestionRepository
from svc.app.datatypes.enums import CompletionStatus, RepetitionTolerance
from svc.app.datatypes.user_behavior_analytic import (
    ActivityCooldownInfo,
    ActivityRepetitionInfo,
    PastActivityContext,
)
from svc.app.models.activity_suggestion import ActivitySuggestion
from svc.app.services.behavior_analytics_service import BehaviorAnalyticsService


class HistoricalActivityAnalyzer:
    def __init__(
        self,
        suggestion_repo: ActivitySuggestionRepository,
        analytics_service: BehaviorAnalyticsService,
    ):
        self.suggestion_repo = suggestion_repo
        self.analytics_service = analytics_service
        self.repetition_rules = self._build_repetition_rules()

    def _build_repetition_rules(self) -> dict:
        """Define repetition tolerance rules for different activity types."""
        return {
            RepetitionTolerance.HIGH: {
                "themes": ["OUTDOOR", "PHYSICAL_ACTIVITY", "NATURE", "READING"],
                "activity_types": ["OUTDOOR", "EXERCISE", "PLAYGROUND"],
                "keywords": [
                    "park",
                    "playground",
                    "walk",
                    "hike",
                    "bike",
                    "read",
                    "library",
                    "beach",
                    "garden",
                ],
                "locations": ["OUTDOOR", "PARK", "BEACH", "TRAIL"],
                "frequency_boost": 1.2,
                "cooldown_weeks": 0,
            },
            RepetitionTolerance.MEDIUM: {
                "themes": ["CREATIVE", "EDUCATIONAL", "SOCIAL"],
                "activity_types": ["CREATIVE", "EDUCATIONAL", "COOKING"],
                "keywords": ["restaurant", "movie", "cooking", "craft", "swimming"],
                "cooldown_weeks": 2,
            },
            RepetitionTolerance.LOW: {
                "themes": ["ENTERTAINMENT", "SPECIAL_EVENT"],
                "activity_types": ["ENTERTAINMENT", "EVENT"],
                "keywords": [
                    "bounce",
                    "arcade",
                    "bowling",
                    "mini golf",
                    "trampoline",
                    "laser tag",
                ],
                "locations": ["INDOOR_ENTERTAINMENT"],
                "cooldown_weeks": 4,
            },
            RepetitionTolerance.VERY_LOW: {
                "themes": ["CULTURAL", "SEASONAL_SPECIAL"],
                "keywords": [
                    "exhibit",
                    "show",
                    "concert",
                    "festival",
                    "fair",
                    "circus",
                ],
                "cooldown_weeks": 12,
            },
        }

    def _classify_activity_repetition_tolerance(
        self, activity: dict
    ) -> RepetitionTolerance:
        """Classify how often an activity can be repeated."""
        activity_lower = {
            "title": activity.get("title", "").lower(),
            "description": activity.get("description", "").lower(),
            "themes": activity.get("themes", []),
            "activity_types": activity.get("activity_types", []),
            "locations": activity.get("locations", []),
        }

        # Check each tolerance level (starting with most restrictive)
        for tolerance in [
            RepetitionTolerance.VERY_LOW,
            RepetitionTolerance.LOW,
            RepetitionTolerance.HIGH,
            RepetitionTolerance.MEDIUM,
        ]:
            rules = self.repetition_rules[tolerance]

            # Check keywords in title/description
            if any(
                keyword in activity_lower["title"]
                or keyword in activity_lower["description"]
                for keyword in rules.get("keywords", [])
            ):
                return tolerance

            # Check themes overlap
            if any(
                theme in activity_lower["themes"] for theme in rules.get("themes", [])
            ):
                return tolerance

            # Check activity types overlap
            if any(
                atype in activity_lower["activity_types"]
                for atype in rules.get("activity_types", [])
            ):
                return tolerance

            # Check locations overlap
            if any(
                loc in activity_lower["locations"] for loc in rules.get("locations", [])
            ):
                return tolerance

        return RepetitionTolerance.MEDIUM  # Default

    def get_relevant_past_activities(
        self, user_id: int, lookback_weeks: int = 8
    ) -> PastActivityContext:
        """Get intelligent past activity context for recommendations."""
        suggestions = self.suggestion_repo.get_user_suggestions(
            user_id, lookback_weeks, include_activity_data=True
        )

        if not suggestions:
            return PastActivityContext()

        # Get user behavior patterns
        analytics = self.analytics_service.analytics_repo.get_by_user(user_id)
        user_patterns = (
            analytics.to_dict()
            if analytics
            else {"marks_big_only": True, "marking_rate": 0.1}
        )

        # Classify activities with smart inference
        classified = self._classify_recent_activities_with_smart_inference(
            suggestions, user_patterns
        )

        return PastActivityContext(
            encourage_repetition=classified["encourage"],
            moderate_cooldown=classified["moderate_cooldown"],
            avoid_repetition=classified["avoid_repetition"],
            successful_patterns=self._analyze_successful_patterns(suggestions),
            avoided_patterns=self._analyze_avoided_patterns(suggestions),
            favorite_themes=self._get_favorite_themes(suggestions),
            preferred_durations=self._get_preferred_durations(suggestions),
        )

    def _classify_recent_activities_with_smart_inference(
        self, suggestions: List[ActivitySuggestion], user_patterns: dict
    ) -> dict:
        """Classify activities using smart completion inference."""
        classified = {"encourage": [], "moderate_cooldown": [], "avoid_repetition": []}

        activity_completion_estimates = {}

        for suggestion in suggestions:
            activity_id = suggestion.activity_id
            activity_data = suggestion.activity.__dict__ if suggestion.activity else {}

            # Get repetition tolerance
            tolerance = self._classify_activity_repetition_tolerance(activity_data)

            # Infer completion status
            inferred_status = self._infer_completion_status(suggestion, user_patterns)

            # Track completion patterns
            if activity_id not in activity_completion_estimates:
                activity_completion_estimates[activity_id] = {
                    "suggested": 0,
                    "estimated_completed": 0,
                    "explicitly_completed": 0,
                    "confidence_level": 0.5,
                    "activity_data": activity_data,
                }

            activity_completion_estimates[activity_id]["suggested"] += 1

            # Weight different completion signals
            if inferred_status == CompletionStatus.COMPLETED:
                activity_completion_estimates[activity_id]["estimated_completed"] += 1.0
                activity_completion_estimates[activity_id][
                    "explicitly_completed"
                ] += 1.0
                activity_completion_estimates[activity_id]["confidence_level"] = 1.0
            elif inferred_status == CompletionStatus.LIKELY_COMPLETED:
                activity_completion_estimates[activity_id]["estimated_completed"] += 0.8
                activity_completion_estimates[activity_id]["confidence_level"] = 0.8
            elif inferred_status == CompletionStatus.POSSIBLY_COMPLETED:
                activity_completion_estimates[activity_id]["estimated_completed"] += 0.6
                activity_completion_estimates[activity_id]["confidence_level"] = 0.6
            elif inferred_status == CompletionStatus.WEATHER_PREVENTED:
                activity_completion_estimates[activity_id]["confidence_level"] = 0.3
            elif inferred_status in [
                CompletionStatus.LIKELY_SKIPPED,
                CompletionStatus.ASSUMED_SKIPPED,
            ]:
                activity_completion_estimates[activity_id]["confidence_level"] = 0.7

        # Classify based on tolerance + estimated completion + confidence
        for activity_id, completion_data in activity_completion_estimates.items():
            activity_data = completion_data["activity_data"]
            tolerance = self._classify_activity_repetition_tolerance(activity_data)

            estimated_completion_rate = (
                completion_data["estimated_completed"] / completion_data["suggested"]
                if completion_data["suggested"] > 0
                else 0
            )

            confidence = completion_data["confidence_level"]
            explicit_completions = completion_data["explicitly_completed"]

            # HIGH tolerance activities: encourage if working
            if tolerance == RepetitionTolerance.HIGH:
                if estimated_completion_rate >= 0.5 or explicit_completions >= 1:
                    classified["encourage"].append(
                        ActivityRepetitionInfo(
                            activity_id=activity_id,
                            activity_title=activity_data.get(
                                "title", "Unknown Activity"
                            ),
                            completion_rate=estimated_completion_rate,
                            frequency=completion_data["suggested"],
                            last_suggested=self._get_last_suggested_date(
                                activity_id, suggestions
                            ),
                            recommendation=self._generate_encouragement_reason(
                                activity_data,
                                estimated_completion_rate,
                                explicit_completions,
                                user_patterns,
                            ),
                            tolerance_level=tolerance,
                        )
                    )

            # MEDIUM tolerance: standard cooldown
            elif tolerance == RepetitionTolerance.MEDIUM:
                weeks_since_last = self._weeks_since_last_suggested(
                    activity_id, suggestions
                )
                cooldown_needed = self.repetition_rules[tolerance]["cooldown_weeks"]

                if (
                    weeks_since_last < cooldown_needed
                    and estimated_completion_rate > 0.4
                ):
                    classified["moderate_cooldown"].append(
                        ActivityCooldownInfo(
                            activity_id=activity_id,
                            activity_title=activity_data.get(
                                "title", "Unknown Activity"
                            ),
                            weeks_until_available=cooldown_needed - weeks_since_last,
                            reason=f"Moderate activity - estimated {estimated_completion_rate:.0%} completion rate, applying {cooldown_needed}-week cooldown",
                            tolerance_level=tolerance,
                        )
                    )

            # LOW/VERY_LOW tolerance: longer cooldown
            else:
                weeks_since_last = self._weeks_since_last_suggested(
                    activity_id, suggestions
                )
                cooldown_needed = self.repetition_rules[tolerance]["cooldown_weeks"]

                if (
                    weeks_since_last < cooldown_needed
                    and estimated_completion_rate > 0.3
                ):
                    classified["avoid_repetition"].append(
                        ActivityCooldownInfo(
                            activity_id=activity_id,
                            activity_title=activity_data.get(
                                "title", "Unknown Activity"
                            ),
                            weeks_until_available=cooldown_needed - weeks_since_last,
                            reason=f"Entertainment venue - avoiding repetition (estimated {estimated_completion_rate:.0%} recent completion)",
                            tolerance_level=tolerance,
                        )
                    )

        return classified

    def _infer_completion_status(
        self, suggestion: ActivitySuggestion, user_patterns: dict
    ) -> CompletionStatus:
        """Infer completion status using multiple signals."""
        # Direct indicators
        if suggestion.completion_status == "completed":
            return CompletionStatus.COMPLETED
        if suggestion.completion_status == "explicitly_skipped":
            return CompletionStatus.EXPLICITLY_SKIPPED

        activity = suggestion.activity.__dict__ if suggestion.activity else {}
        days_since_suggested = (datetime.now().date() - suggestion.suggested_date).days

        # User behavior analysis
        marks_big_only = user_patterns.get("marks_big_only", True)
        is_big_activity = self.analytics_service._is_big_activity(suggestion.activity)

        # If user only marks big activities and this IS big but unmarked
        if marks_big_only and is_big_activity and days_since_suggested > 3:
            return CompletionStatus.LIKELY_SKIPPED

        # If user only marks big activities and this is NOT big
        if marks_big_only and not is_big_activity:
            return self._infer_small_activity_completion(suggestion, user_patterns)

        # Default time-based inference
        if days_since_suggested > 21:
            return CompletionStatus.ASSUMED_SKIPPED
        elif days_since_suggested > 14:
            return CompletionStatus.LIKELY_SKIPPED
        elif days_since_suggested <= 3:
            return CompletionStatus.PENDING
        else:
            return CompletionStatus.UNKNOWN

    def _infer_small_activity_completion(
        self, suggestion: ActivitySuggestion, user_patterns: dict
    ) -> CompletionStatus:
        """Infer completion for small activities using behavioral patterns."""
        activity = suggestion.activity.__dict__ if suggestion.activity else {}
        days_since_suggested = (datetime.now().date() - suggestion.suggested_date).days

        completion_likelihood = 0.6  # Base likelihood

        # Weather-dependent activities
        if self._is_weather_dependent(activity):
            if suggestion.weather_conditions and suggestion.weather_conditions.get(
                "suitable_for_outdoor", True
            ):
                completion_likelihood += 0.2
            else:
                return CompletionStatus.WEATHER_PREVENTED

        # High-repetition activities (parks, walks)
        tolerance = self._classify_activity_repetition_tolerance(activity)
        if tolerance == RepetitionTolerance.HIGH:
            completion_likelihood += 0.3

        # Free/low cost activities
        if activity.get("costs") and any(
            cost in ["FREE", "LOW"] for cost in activity.get("costs", [])
        ):
            completion_likelihood += 0.2

        # Time-based adjustments
        if days_since_suggested <= 7:
            completion_likelihood += 0.1
        elif days_since_suggested > 14:
            completion_likelihood -= 0.2

        # Clamp to 0-1
        completion_likelihood = max(0.0, min(1.0, completion_likelihood))

        if completion_likelihood >= 0.8:
            return CompletionStatus.LIKELY_COMPLETED
        elif completion_likelihood >= 0.6:
            return CompletionStatus.POSSIBLY_COMPLETED
        elif completion_likelihood >= 0.4:
            return CompletionStatus.UNKNOWN
        else:
            return CompletionStatus.LIKELY_SKIPPED

    def _is_weather_dependent(self, activity: dict) -> bool:
        """Check if activity is weather dependent."""
        outdoor_indicators = [
            "OUTDOOR" in activity.get("themes", []),
            "OUTDOOR" in activity.get("activity_types", []),
            "PARK" in activity.get("locations", []),
            any(
                keyword in activity.get("title", "").lower()
                for keyword in ["park", "beach", "hike", "bike", "outdoor"]
            ),
        ]
        return any(outdoor_indicators)

    def _get_last_suggested_date(
        self, activity_id: int, suggestions: List[ActivitySuggestion]
    ) -> Optional[date]:
        """Get the last suggested date for an activity."""
        activity_suggestions = [s for s in suggestions if s.activity_id == activity_id]
        return (
            max(s.suggested_date for s in activity_suggestions)
            if activity_suggestions
            else None
        )

    def _weeks_since_last_suggested(
        self, activity_id: int, suggestions: List[ActivitySuggestion]
    ) -> int:
        """Get weeks since activity was last suggested."""
        last_date = self._get_last_suggested_date(activity_id, suggestions)
        if not last_date:
            return 999  # Very large number if never suggested
        return (datetime.now().date() - last_date).days // 7

    def _generate_encouragement_reason(
        self,
        activity_data: dict,
        completion_rate: float,
        explicit_completions: int,
        user_patterns: dict,
    ) -> str:
        """Generate contextual reasons for encouraging activity repetition."""
        activity_title = activity_data.get("title", "Activity")

        if explicit_completions > 0:
            return f"Family marked this as completed {explicit_completions} time(s) - clearly enjoyed it and can be repeated regularly"

        if completion_rate >= 0.8 and user_patterns.get("marks_big_only"):
            return "Strong behavioral signals suggest family regularly enjoys this type of activity, perfect for weekly routine"

        if self._is_weather_dependent(activity_data):
            return "Great outdoor activity that family seems to do when weather permits - excellent for active family time"

        if any(cost in ["FREE", "LOW"] for cost in activity_data.get("costs", [])):
            return "Budget-friendly activity that appears to be part of family's regular routine - continue the healthy habit"

        return "Activity patterns suggest this works well for your family and can be enjoyed regularly"

    def _analyze_successful_patterns(
        self, suggestions: List[ActivitySuggestion]
    ) -> dict:
        """Analyze patterns in successful activities."""
        successful = [
            s
            for s in suggestions
            if s.completion_status in ["completed", "likely_completed"]
        ]

        if not successful:
            return {}

        patterns = {
            "most_successful_themes": self._get_theme_distribution(successful),
            "most_successful_activity_types": self._get_activity_type_distribution(
                successful
            ),
            "preferred_time_patterns": self._analyze_timing_patterns(successful),
            "weather_preferences": self._analyze_weather_patterns(successful),
        }

        return patterns

    def _analyze_avoided_patterns(self, suggestions: List[ActivitySuggestion]) -> dict:
        """Analyze patterns in avoided activities."""
        avoided = [
            s
            for s in suggestions
            if s.completion_status
            in ["likely_skipped", "assumed_skipped", "explicitly_skipped"]
        ]

        if not avoided:
            return {}

        patterns = {
            "avoided_themes": self._get_theme_distribution(avoided),
            "avoided_activity_types": self._get_activity_type_distribution(avoided),
            "problematic_timing": self._analyze_timing_patterns(avoided),
        }

        return patterns

    def _get_favorite_themes(
        self, suggestions: List[ActivitySuggestion]
    ) -> List[tuple[str, int]]:
        """Get favorite themes based on completion patterns."""
        theme_counts = {}
        for suggestion in suggestions:
            if not suggestion.activity or not suggestion.activity.themes:
                continue

            is_successful = suggestion.completion_status in [
                "completed",
                "likely_completed",
            ]
            if is_successful:
                for theme in suggestion.activity.themes:
                    theme_counts[theme] = theme_counts.get(theme, 0) + 1

        return sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    def _get_preferred_durations(
        self, suggestions: List[ActivitySuggestion]
    ) -> List[str]:
        """Get preferred activity durations."""
        duration_success = {}
        for suggestion in suggestions:
            if not suggestion.activity or not suggestion.activity.durations:
                continue

            is_successful = suggestion.completion_status in [
                "completed",
                "likely_completed",
            ]
            for duration in suggestion.activity.durations:
                if duration not in duration_success:
                    duration_success[duration] = {"total": 0, "successful": 0}
                duration_success[duration]["total"] += 1
                if is_successful:
                    duration_success[duration]["successful"] += 1

        # Sort by success rate
        sorted_durations = sorted(
            duration_success.items(),
            key=lambda x: (
                x[1]["successful"] / x[1]["total"] if x[1]["total"] > 0 else 0
            ),
            reverse=True,
        )

        return [duration for duration, _ in sorted_durations[:3]]

    def _get_theme_distribution(self, suggestions: List[ActivitySuggestion]) -> dict:
        """Get theme distribution for suggestions."""
        theme_counts = {}
        for suggestion in suggestions:
            if suggestion.activity and suggestion.activity.themes:
                for theme in suggestion.activity.themes:
                    theme_counts[theme] = theme_counts.get(theme, 0) + 1
        return theme_counts

    def _get_activity_type_distribution(
        self, suggestions: List[ActivitySuggestion]
    ) -> dict:
        """Get activity type distribution for suggestions."""
        type_counts = {}
        for suggestion in suggestions:
            if suggestion.activity and suggestion.activity.activity_types:
                for atype in suggestion.activity.activity_types:
                    type_counts[atype] = type_counts.get(atype, 0) + 1
        return type_counts

    def _analyze_timing_patterns(self, suggestions: List[ActivitySuggestion]) -> dict:
        """Analyze timing patterns in suggestions."""
        # This would analyze day of week, season, etc.
        # Implementation depends on additional data you track
        return {}

    def _analyze_weather_patterns(self, suggestions: List[ActivitySuggestion]) -> dict:
        """Analyze weather patterns for successful activities."""
        # Implementation depends on weather data storage
        return {}
