import json
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from svc.app.dal.activity_repository import ActivityRepository
from svc.app.dal.activity_suggestion_repository import ActivitySuggestionRepository
from svc.app.datatypes.enums import WeatherDay
from svc.app.datatypes.family_preference import FamilyProfile
from svc.app.datatypes.user_behavior_analytic import (
    ActivityCooldownInfo,
    ActivityRepetitionInfo,
    PastActivityContext,
    WeeklyContext,
)
from svc.app.services.activity_suggestion_service import HistoricalActivityAnalyzer
from svc.app.services.family_profile_service import FamilyProfileService
from svc.app.services.weather_service import WeatherService

logger = logging.getLogger(__name__)


class EnhancedActivityPlannerService:
    def __init__(
        self,
        family_profile_service: FamilyProfileService,
        activity_repo: ActivityRepository,
        suggestion_repo: ActivitySuggestionRepository,
        historical_analyzer: HistoricalActivityAnalyzer,
        weather_service: WeatherService,
        llm_client,
    ):
        self.family_profile_service = family_profile_service
        self.activity_repo = activity_repo
        self.suggestion_repo = suggestion_repo
        self.historical_analyzer = historical_analyzer
        self.weather_service = weather_service
        self.llm_client = llm_client
        self.model = "claude-sonnet-4-20250514"
        self.temperature = 0.7
        self.max_retries = 3

    async def plan_weekly_activities(
        self, user_id: int, target_week: Optional[date] = None
    ) -> List[dict]:
        """Plan weekly activities for a family."""
        try:
            # 1. Gather all required data
            family_profile = self.family_profile_service.get_family_profile(user_id)
            weekly_context = await self._build_weekly_context(
                family_profile, target_week
            )
            available_activities = await self._get_filtered_activities(
                family_profile, weekly_context
            )
            past_context = self.historical_analyzer.get_relevant_past_activities(
                user_id
            )

            # 2. Generate LLM recommendations
            planned_activities = await self._generate_llm_recommendations(
                family_profile, weekly_context, available_activities, past_context
            )

            # 3. Validate and enhance recommendations
            validated_activities = self._validate_and_enhance_recommendations(
                planned_activities, family_profile
            )

            # 4. Record suggestions for future learning
            await self._record_suggestions(
                user_id, validated_activities, weekly_context
            )

            return validated_activities

        except Exception as e:
            logger.error(f"Error planning activities for user {user_id}: {e}")
            raise

    async def _build_weekly_context(
        self, family_profile: FamilyProfile, target_week: Optional[date]
    ) -> WeeklyContext:
        """Build weekly context with weather and other factors."""
        if not target_week:
            target_week = datetime.now().date()
            # Adjust to start of week (Monday)
            days_since_monday = target_week.weekday()
            target_week = target_week - timedelta(days=days_since_monday)

        # Get weather forecast
        weather_forecast = []
        if family_profile.home_coordinates:
            try:
                weather_forecast = self.weather_service.get_weekly_forecast(
                    family_profile.home_location, target_week
                )
            except Exception as e:
                logger.warning(f"Could not get weather forecast: {e}")

        # Determine season
        season = self._get_season(target_week)

        # Get school schedule (placeholder - implement based on your needs)
        school_schedule = self._get_school_schedule(target_week)

        return WeeklyContext(
            target_week_start=target_week,
            weather_forecast=weather_forecast,
            season=season,
            school_schedule=school_schedule,
        )

    async def _get_filtered_activities(
        self, family_profile: FamilyProfile, weekly_context: WeeklyContext
    ) -> List[dict]:
        """Get activities filtered by family profile and context."""
        # Get age ranges from kids
        age_ranges = [(kid["age"] - 1, kid["age"] + 1) for kid in family_profile.kids]

        # Get activities from repository
        activities = self.activity_repo.get_filtered_activities(
            user_location=family_profile.home_coordinates,
            max_distance=family_profile.max_travel_distance,
            age_ranges=age_ranges,
            themes=(
                family_profile.preferred_themes
                if family_profile.preferred_themes
                else None
            ),
            activity_types=(
                family_profile.preferred_activity_types
                if family_profile.preferred_activity_types
                else None
            ),
            cost_ranges=(
                family_profile.preferred_cost_ranges
                if family_profile.preferred_cost_ranges
                else None
            ),
        )

        # Convert to dicts for LLM processing
        return [self._activity_to_dict(activity) for activity in activities]

    async def _generate_llm_recommendations(
        self,
        family_profile: FamilyProfile,
        weekly_context: WeeklyContext,
        available_activities: List[dict],
        past_context: PastActivityContext,
    ) -> List[dict]:
        """Generate recommendations using LLM."""

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            family_profile, weekly_context, available_activities, past_context
        )

        for attempt in range(self.max_retries):
            try:
                response = await self.llm_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=self.temperature,
                    max_tokens=2000,
                )

                content = response.choices[0].message.content
                if not content:
                    raise ValueError("Empty response from LLM")

                # Parse JSON response
                import json

                try:
                    activities = json.loads(content.strip())
                except json.JSONDecodeError:
                    # Try to extract JSON from response if wrapped in markdown
                    import re

                    json_match = re.search(
                        r"```(?:json)?\s*(\[.*?\])\s*```", content, re.DOTALL
                    )
                    if json_match:
                        activities = json.loads(json_match.group(1))
                    else:
                        raise

                if not isinstance(activities, list):
                    raise ValueError("Response is not a JSON array")

                return activities

            except Exception as e:
                logger.warning(f"LLM attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise ValueError(
                        f"Failed to get LLM recommendations after {self.max_retries} attempts"
                    )

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM."""
        return """You are an expert Family Activity Planner AI with deep understanding of activity repetition patterns and family preferences.

CORE PRINCIPLE: Not all repetition is bad. Some activities (parks, walks, reading) are MEANT to be repeated frequently and become better with consistency. Others (specific venues, events) become stale with too much repetition.

Your expertise:
- Recognizing which activities benefit from repetition vs. those that don't
- Child development and age-appropriate activities  
- Balancing educational, physical, creative, and social activities
- Weather and seasonal considerations
- Family dynamics and logistics

REPETITION INTELLIGENCE:
- ENCOURAGE repeating activities marked as "encourage_repetition" - these are working well and should continue
- RESPECT cooldown periods for activities in "moderate_cooldown" and "avoid_repetition"
- PRIORITIZE activities similar to those in "successful_patterns"
- AVOID patterns identified in "avoided_patterns"

SELECTION CRITERIA (in order of importance):
1. FAMILY FAVORITES: Strongly prioritize activities similar to "encourage_repetition" list
2. AGE APPROPRIATENESS: Activities must match children's ages and developmental stages
3. VARIETY BALANCE: Include mix of indoor/outdoor, active/quiet, educational/fun
4. PRACTICAL FEASIBILITY: Consider weather, location, transportation, and budget
5. INTELLIGENT REPETITION: Use repetition patterns to inform choices
6. SEASONAL RELEVANCE: Choose activities that make sense for current season/weather

QUALITY STANDARDS:
- Each activity should serve a clear developmental or family bonding purpose
- Consider the full week's energy levels (balance high-energy with calming activities)
- Build on successful patterns while introducing appropriate variety
- Ensure activities are realistic for family's constraints and capabilities

OUTPUT REQUIREMENTS:
- Return exactly 4-7 activities
- Each activity must include a compelling, specific "why_it_fits" explanation that references family patterns when relevant
- Use provided activity IDs only

Return ONLY valid JSON array with no additional text:
[{"id": int, "title": string, "why_it_fits": string}]"""

    def _build_user_prompt(
        self,
        family_profile: FamilyProfile,
        weekly_context: WeeklyContext,
        available_activities: List[dict],
        past_context: PastActivityContext,
    ) -> str:
        """Build the user prompt with all context information."""

        # Build family description
        kids_desc = ", ".join([f"age {kid['age']}" for kid in family_profile.kids])
        family_desc = f"""FAMILY PROFILE:
- {family_profile.family_size} family members ({family_profile.adults_count} adults, {len(family_profile.kids)} children: {kids_desc})
- Location: {family_profile.home_location}
- Available days: {', '.join(family_profile.available_days)}
- Budget preference: {', '.join(family_profile.preferred_cost_ranges)}
- Transportation: {'Car available' if family_profile.has_car else 'Public transit/walking only'}
- Max travel distance: {family_profile.max_travel_distance} miles"""

        # Build context description
        weather_summary = self._summarize_weather_forecast(
            weekly_context.weather_forecast
        )
        context_desc = f"""WEEKLY CONTEXT:
- Week starting: {weekly_context.target_week_start.strftime('%B %d, %Y')}
- Season: {weekly_context.season}
- Weather outlook: {weather_summary}
- School status: {weekly_context.school_schedule or 'Unknown'}"""

        # Build repetition guidance
        repetition_desc = f"""REPETITION GUIDANCE:

ENCOURAGE REPETITION (these are family favorites - prioritize similar activities):
{self._format_encourage_list(past_context.encourage_repetition)}

MODERATE COOLDOWN (good activities, but wait before repeating):  
{self._format_cooldown_list(past_context.moderate_cooldown)}

AVOID REPETITION (done too recently):
{self._format_avoid_list(past_context.avoid_repetition)}

SUCCESSFUL PATTERNS TO BUILD ON:
{self._format_successful_patterns(past_context.successful_patterns)}"""

        # Build preferences
        theme_prefs = (
            ", ".join(family_profile.preferred_themes)
            if family_profile.preferred_themes
            else "None specified"
        )
        activity_type_prefs = (
            ", ".join(family_profile.preferred_activity_types)
            if family_profile.preferred_activity_types
            else "None specified"
        )
        favorite_themes = ", ".join(
            [
                f"{theme} ({count}x successful)"
                for theme, count in past_context.favorite_themes[:3]
            ]
        )

        preferences_desc = f"""FAMILY PREFERENCES:
- Preferred themes: {theme_prefs}
- Preferred activity types: {activity_type_prefs}
- Most successful themes historically: {favorite_themes or 'Not enough data yet'}
- Preferred durations: {', '.join(past_context.preferred_durations) or 'No clear preference'}
- Group activity comfort: {family_profile.group_activity_comfort}
- Openness to new experiences: {family_profile.new_experience_openness}"""

        # Activity database summary
        activities_desc = f"""AVAILABLE ACTIVITIES DATABASE:
{len(available_activities)} activities available. Focus on activities that match successful patterns while respecting repetition guidelines above.

Activities to choose from: {json.dumps(available_activities, indent=2)}"""

        return f"{family_desc}\n\n{context_desc}\n\n{repetition_desc}\n\n{preferences_desc}\n\n{activities_desc}"

    def _summarize_weather_forecast(self, forecast: List[WeatherDay]) -> str:
        """Summarize weather forecast for the week."""
        if not forecast:
            return "Weather data unavailable"

        outdoor_suitable_days = sum(1 for day in forecast if day.suitable_for_outdoor)
        conditions = [day.condition for day in forecast]

        return f"{outdoor_suitable_days}/{len(forecast)} days suitable for outdoor activities. Conditions: {', '.join(set(conditions))}"

    def _format_encourage_list(
        self, encourage_list: List[ActivityRepetitionInfo]
    ) -> str:
        """Format the encourage repetition list for the prompt."""
        if not encourage_list:
            return "- None identified yet - this is a new family!"

        formatted = []
        for item in encourage_list[:5]:  # Top 5
            formatted.append(
                f"- {item.activity_title} (completed {item.completion_rate:.0%} of the time) - {item.recommendation}"
            )
        return "\n".join(formatted)

    def _format_cooldown_list(self, cooldown_list: List[ActivityCooldownInfo]) -> str:
        """Format the cooldown list for the prompt."""
        if not cooldown_list:
            return "- No activities in cooldown"

        formatted = []
        for item in cooldown_list[:5]:
            formatted.append(
                f"- {item.activity_title} - wait {item.weeks_until_available} more weeks"
            )
        return "\n".join(formatted)

    def _format_avoid_list(self, avoid_list: List[ActivityCooldownInfo]) -> str:
        """Format the avoid repetition list for the prompt."""
        if not avoid_list:
            return "- No activities to avoid"

        formatted = []
        for item in avoid_list[:5]:
            formatted.append(f"- {item.activity_title} - {item.reason}")
        return "\n".join(formatted)

    def _format_successful_patterns(self, patterns: Dict[str, Any]) -> str:
        """Format successful patterns for the prompt."""
        if not patterns:
            return "- Not enough historical data yet"

        formatted = []

        if patterns.get("most_successful_themes"):
            top_themes = sorted(
                patterns["most_successful_themes"].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:3]
            formatted.append(
                f"- Most successful themes: {', '.join([f'{theme} ({count}x)' for theme, count in top_themes])}"
            )

        if patterns.get("most_successful_activity_types"):
            top_types = sorted(
                patterns["most_successful_activity_types"].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:3]
            formatted.append(
                f"- Most successful activity types: {', '.join([f'{atype} ({count}x)' for atype, count in top_types])}"
            )

        return (
            "\n".join(formatted)
            if formatted
            else "- Building pattern recognition from family's preferences"
        )

    def _validate_and_enhance_recommendations(
        self, planned_activities: List[dict], family_profile: FamilyProfile
    ) -> List[dict]:
        """Validate and enhance the LLM recommendations."""
        validated = []

        for activity in planned_activities:
            # Validate required fields
            if not all(key in activity for key in ["id", "title", "why_it_fits"]):
                logger.warning(
                    f"Skipping malformed activity recommendation: {activity}"
                )
                continue

            # Validate activity ID exists
            # This would check against your activity database
            # For now, we'll assume all IDs are valid

            # Enhance with additional metadata
            enhanced_activity = {
                **activity,
                "recommended_date": None,  # You could add smart date suggestions
                "priority_score": self._calculate_priority_score(
                    activity, family_profile
                ),
                "estimated_duration": None,  # Could extract from activity data
                "weather_dependency": None,  # Could extract from activity data
            }

            validated.append(enhanced_activity)

        # Ensure we have 4-7 activities
        if len(validated) < 4:
            logger.warning(
                f"Only {len(validated)} activities recommended, below minimum of 4"
            )
        elif len(validated) > 7:
            logger.warning(
                f"{len(validated)} activities recommended, above maximum of 7"
            )
            validated = validated[:7]  # Trim to 7

        return validated

    def _calculate_priority_score(
        self, activity: dict, family_profile: FamilyProfile
    ) -> float:
        """Calculate a priority score for the activity."""
        score = 0.5  # Base score

        # This is a placeholder - you could implement sophisticated scoring
        # based on family preferences, past success rates, etc.

        return min(1.0, max(0.0, score))

    async def _record_suggestions(
        self, user_id: int, activities: List[dict], weekly_context: WeeklyContext
    ) -> None:
        """Record the suggestions for future learning."""
        suggestions_data = []

        for activity in activities:
            suggestion_data = {
                "user_id": user_id,
                "activity_id": activity["id"],
                "suggested_date": datetime.now().date(),
                "target_week_start": weekly_context.target_week_start,
                "suggested_reason": activity.get("why_it_fits"),
                "weather_conditions": {
                    "forecast_summary": self._summarize_weather_forecast(
                        weekly_context.weather_forecast
                    ),
                    "season": weekly_context.season,
                },
            }
            suggestions_data.append(suggestion_data)

        self.suggestion_repo.create_suggestions(suggestions_data)
        logger.info(
            f"Recorded {len(suggestions_data)} activity suggestions for user {user_id}"
        )

    def _activity_to_dict(self, activity) -> dict:
        """Convert Activity model to dict for LLM processing."""
        return {
            "id": activity.id,
            "title": activity.title,
            "description": activity.description,
            "themes": activity.themes or [],
            "activity_types": activity.activity_types or [],
            "costs": activity.costs or [],
            "durations": activity.durations or [],
            "locations": activity.locations or [],
            "age_groups": activity.age_groups or [],
            "primary_type": activity.primary_type,
            "primary_theme": activity.primary_theme,
        }

    def _get_season(self, date_obj: date) -> str:
        """Determine the season for a given date."""
        month = date_obj.month
        if month in [12, 1, 2]:
            return "Winter"
        elif month in [3, 4, 5]:
            return "Spring"
        elif month in [6, 7, 8]:
            return "Summer"
        else:
            return "Fall"

    def _get_school_schedule(self, date_obj: date) -> str:
        """Determine school schedule status."""
        # This is a placeholder - implement based on your local school calendar
        month = date_obj.month
        if month in [6, 7, 8]:
            return "summer_break"
        elif month in [12, 1] and date_obj.day < 15:
            return "winter_break"
        else:
            return "in_session"
