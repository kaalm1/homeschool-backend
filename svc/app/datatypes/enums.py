from enum import Enum


# ---------------------------
# UI enums
# ---------------------------
class Cost(str, Enum):
    FREE = "Free"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Duration(str, Enum):
    SHORT = "Short"
    MEDIUM = "Medium"
    LONG = "Long"
    FULL_DAY = "Full Day"
    MULTI_DAY = "Multi-Day"


class Participants(str, Enum):
    SOLO = "Solo"
    TWO_PLAYER = "2 Players"
    SMALL_GROUP = "3–5"
    MEDIUM_GROUP = "6–10"
    LARGE_GROUP = "10+"
    FAMILY = "Family"


class AgeGroup(str, Enum):
    TODDLER = "Toddler"
    CHILD = "Child"
    TWEEN = "Tween"
    TEEN = "Teen"
    ADULT = "Adult"
    FAMILY = "Family"


class Location(str, Enum):
    HOME_INDOOR = "Home Indoor"
    HOME_OUTDOOR = "Home Outdoor"
    LOCAL = "Local"
    REGIONAL = "Regional"
    TRAVEL = "Travel"


class Season(str, Enum):
    ALL = "All"
    SPRING = "Spring"
    SUMMER = "Summer"
    FALL = "Fall"
    WINTER = "Winter"
    RAINY_DAY = "Rainy Day"
    SNOWY_DAY = "Snowy Day"


# ---------------------------
# AI mapping
# ---------------------------
COST_TO_AI = {
    Cost.FREE: "Free",
    Cost.LOW: "Low ($)",
    Cost.MEDIUM: "Medium ($$)",
    Cost.HIGH: "High ($$$)",
}

DURATION_TO_AI = {
    Duration.SHORT: "Short (<30m)",
    Duration.MEDIUM: "Medium (30–90m)",
    Duration.LONG: "Long (2–3h)",
    Duration.FULL_DAY: "Full Day",
    Duration.MULTI_DAY: "Multi-Day",
}

PARTICIPANTS_TO_AI = {
    Participants.SOLO: "Solo",
    Participants.TWO_PLAYER: "2 Players",
    Participants.SMALL_GROUP: "3–5 participants",
    Participants.MEDIUM_GROUP: "6–10 participants",
    Participants.LARGE_GROUP: "10+ participants",
    Participants.FAMILY: "Family (mixed ages)",
}

AGEGROUP_TO_AI = {
    AgeGroup.TODDLER: "Toddler (2–4)",
    AgeGroup.CHILD: "Child (5–8)",
    AgeGroup.TWEEN: "Tween (9–12)",
    AgeGroup.TEEN: "Teen (13–17)",
    AgeGroup.ADULT: "Adult (18+)",
    AgeGroup.FAMILY: "Family (mixed ages)",
}

LOCATION_TO_AI = {
    Location.HOME_INDOOR: "Home (Indoor)",
    Location.HOME_OUTDOOR: "Home (Outdoor)",
    Location.LOCAL: "Local (≤30 min drive)",
    Location.REGIONAL: "Regional (≤2 hr drive)",
    Location.TRAVEL: "Travel / Destination",
}

SEASON_TO_AI = {
    Season.ALL: "All Seasons",
    Season.SPRING: "Spring",
    Season.SUMMER: "Summer",
    Season.FALL: "Fall",
    Season.WINTER: "Winter",
    Season.RAINY_DAY: "Rainy Day",
    Season.SNOWY_DAY: "Snowy Day",
}
