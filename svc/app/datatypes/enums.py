from enum import Enum
from typing import Any, Dict, List, Optional


class FilterEnum(str, Enum):
    db_value: str
    label: str
    ai_value: str

    def __new__(cls, db_value: str, label: str, ai_value: str) -> Any:
        obj = str.__new__(cls, db_value)
        obj._value_ = db_value
        obj.db_value = db_value
        obj.label = label
        obj.ai_value = ai_value
        return obj

    @classmethod
    def to_frontend(cls):
        return [{"value": f.db_value, "label": f.label} for f in cls]

    @classmethod
    def to_ai(cls, db_values):
        return [f.ai_value for f in cls if f.db_value in db_values]

    @classmethod
    def from_ai(cls, ai_values):
        return [f.db_value for f in cls if f.ai_value in ai_values]

    @classmethod
    def from_ai_safe(cls, ai_values: Optional[List[str]]) -> List[str]:
        """Convert AI values to DB values with safe handling of None/empty lists."""
        if not ai_values:
            return []

        db_values = []
        for ai_value in ai_values:
            # Try exact match first
            found = False
            for enum_item in cls:
                if enum_item.ai_value == ai_value:
                    db_values.append(enum_item.db_value)
                    found = True
                    break

            # Try case-insensitive partial match
            if not found:
                ai_value_lower = ai_value.lower()
                for enum_item in cls:
                    if (
                        ai_value_lower in enum_item.ai_value.lower()
                        or enum_item.ai_value.lower() in ai_value_lower
                    ):
                        db_values.append(enum_item.db_value)
                        found = True
                        break

            if not found:
                # Log unmatched values but continue processing
                print(
                    f"Warning: Could not match '{ai_value}' to any {cls.__name__} value"
                )

        return db_values

    @classmethod
    def bulk_convert_from_ai(cls, tagged_data: dict) -> dict:
        """Convert multiple AI value lists to DB values in a dictionary."""
        converted_data = {}

        # Map of field names to their corresponding enum classes
        field_enum_map = {
            "themes": Theme,
            "activity_types": ActivityType,
            "costs": Cost,
            "durations": Duration,
            "participants": Participants,
            "locations": Location,
            "seasons": Season,
            "age_groups": AgeGroup,
            "frequency": Frequency,
        }

        for field_name, enum_class in field_enum_map.items():
            if field_name in tagged_data:
                converted_data[field_name] = enum_class.from_ai_safe(
                    tagged_data[field_name]
                )
            else:
                converted_data[field_name] = []

        # Copy non-enum fields as-is
        for key, value in tagged_data.items():
            if key not in field_enum_map:
                converted_data[key] = value

        return converted_data


# ---------------------------
# UI enums
# ---------------------------
class Cost(FilterEnum):
    FREE = ("free", "Free", "free")
    LOW = ("low", "$", "cheap or budget-friendly")
    MEDIUM = ("medium", "$$", "moderately priced")
    HIGH = ("high", "$$$", "expensive or premium")


class Duration(FilterEnum):
    SHORT = ("short", "Short", "short activity under 1 hour")
    MEDIUM = ("medium", "Medium", "activity lasting a few hours")
    LONG = ("long", "Long", "half-day activity")
    FULL_DAY = ("full_day", "Full Day", "full-day activity")
    MULTI_DAY = ("multi_day", "Multi-Day", "multi-day activity or trip")


class Participants(FilterEnum):
    SOLO = ("solo", "Solo", "single person activity")
    TWO_PLAYER = ("two_player", "2 Players", "activity for two people")
    SMALL_GROUP = ("small_group", "3–5", "small group activity")
    MEDIUM_GROUP = ("medium_group", "6–10", "medium-sized group activity")
    LARGE_GROUP = ("large_group", "10+", "large group activity")
    FAMILY = ("family", "Family", "family-friendly activity")


class AgeGroup(FilterEnum):
    TODDLER = ("toddler", "Toddler", "for toddlers")
    CHILD = ("child", "Child", "for children")
    TWEEN = ("tween", "Tween", "for tweens")
    TEEN = ("teen", "Teen", "for teenagers")
    ADULT = ("adult", "Adult", "for adults")
    FAMILY = ("family", "Family", "suitable for whole family")


class Location(FilterEnum):
    HOME_INDOOR = ("home_indoor", "Home Indoor", "indoor at home")
    HOME_OUTDOOR = ("home_outdoor", "Home Outdoor", "outdoor at home")
    LOCAL = ("local", "Local", "local activity nearby")
    REGIONAL = ("regional", "Regional", "regional activity within driving distance")
    TRAVEL = ("travel", "Travel", "requires travel or vacation")


class Season(FilterEnum):
    ALL = ("all", "Year-round", "year-round")
    SPRING = ("spring", "🌸", "springtime activity")
    SUMMER = ("summer", "☀️", "summer activity")
    FALL = ("fall", "🍂", "autumn activity")
    WINTER = ("winter", "❄️", "winter activity")
    RAINY_DAY = ("rainy_day", "🌧️", "rainy day activity")
    SNOWY_DAY = ("snowy_day", "☃️", "snow day activity")


class Frequency(FilterEnum):
    DAILY = ("daily", "Daily", "daily activity")
    WEEKLY = ("weekly", "Weekly", "weekly activity")
    MONTHLY = ("monthly", "Monthly", "monthly activity")
    ANNUALLY = ("annually", "Annually", "annually activity")
    SEASONAL = ("seasonal", "Seasonal", "seasonal activity")


class Theme(FilterEnum):
    ADVENTURE = ("adventure", "🌋 Adventure", "adventurous or exciting activity")
    CREATIVE = ("creative", "🎨 Creative / Arts", "creative, arts, or craft activity")
    EDUCATIONAL = (
        "educational",
        "📚 Educational",
        "educational or learning-focused activity",
    )
    FITNESS = (
        "fitness",
        "💪 Fitness & Sports",
        "exercise, fitness, or physical activity",
    )
    FOOD_DRINK = (
        "food_drink",
        "🍴 Food & Drink",
        "cooking, dining, or food-related activity",
    )
    FESTIVE = ("festive", "🎉 Festive / Celebration", "celebratory or party activity")
    MINDFULNESS = (
        "mindfulness",
        "🧘 Mindfulness",
        "mindful, meditative, or reflective activity",
    )
    NATURE = ("nature", "🌿 Nature", "nature-based activity")
    RELAXATION = ("relaxation", "🛋️ Relaxation", "calm, relaxing, or wellness activity")
    SOCIAL = ("social", "🤝 Social", "social or community activity")


class ActivityType(FilterEnum):
    AMUSEMENT_PARK = (
        "amusement_park",
        "🎢 Amusement Park",
        "visiting amusement park or theme park",
    )
    ARTS_CRAFTS = ("arts_crafts", "🎨 Creative / Arts", "artistic or creative activity")
    BOARD_GAMES = ("board_games", "🎲 Board Games", "board games or tabletop games")
    CLASSES = (
        "classes",
        "📚 Classes / Workshops",
        "instructional or learning activity",
    )
    DANCE = ("dance", "💃 Dance / Movement", "dance or movement activity")
    FESTIVAL = (
        "festival",
        "🎪 Festival / Fair",
        "attending festival, fair, or carnival",
    )
    GAMES = (
        "games",
        "🎲 Games",
        "playing games of any kind, board, card, or group games",
    )
    GARDENING = ("gardening", "🌱 Gardening", "gardening or horticulture activity")
    HIKING = ("hiking", "🥾 Hiking", "going on a hike or trail walk")
    INDOOR = ("indoor", "🏠 Indoor Fun", "indoor recreational activity")
    MUSIC = ("music", "🎶 Music", "music or musical activity")
    OUTDOOR = ("outdoor", "🌳 Outdoor Fun", "outdoor recreational activity")
    PARK = ("park", "🏞️ Park Visit", "visiting a local park or public green space")
    PUZZLES = (
        "puzzles",
        "🧩 Puzzles & Brain Games",
        "puzzle or brain-challenging activity",
    )
    SCIENCE_TECH = (
        "science_tech",
        "🔬 Science & Tech",
        "science, technology, or STEM activity",
    )
    STORYTELLING = (
        "storytelling",
        "📖 Storytelling / Reading",
        "storytelling, reading, or literary activity",
    )
    TRAVEL = ("travel", "✈️ Trips & Excursions", "travel or excursion activity")
    VIDEO_GAMES = ("video_games", "🎮 Video Games", "playing video or digital games")
    VOLUNTEERING = ("volunteering", "🤝 Volunteering", "volunteer or community service")
    SPORTS = ("sports", "🏀 Sports", "sports or physical games")
    ZOO_AQUARIUM = (
        "zoo_aquarium",
        "🦁 Zoo / Aquarium",
        "visiting zoo, aquarium, or wildlife park",
    )


DEFAULT_ENUMS_LLM: Dict[str, Any] = {
    "activity_types": [e.ai_value for e in ActivityType],
    "themes": [e.ai_value for e in Theme],
    "costs": [e.ai_value for e in Cost],
    "durations": [e.ai_value for e in Duration],
    "participants": [e.ai_value for e in Participants],
    "locations": [e.ai_value for e in Location],
    "seasons": [e.ai_value for e in Season],
    "age_groups": [e.ai_value for e in AgeGroup],
    "frequency": [e.ai_value for e in Frequency],
}
