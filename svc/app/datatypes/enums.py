from enum import Enum


class FilterEnum(Enum):
    def __init__(self, db_value: str, label: str, ai_value: str):
        self.db_value = db_value  # stable for DB
        self.label = label  # frontend label
        self.ai_value = ai_value  # AI-friendly phrase

    @classmethod
    def to_frontend(cls):
        return [{"value": f.db_value, "label": f.label} for f in cls]

    @classmethod
    def to_ai(cls, db_values):
        return [f.ai_value for f in cls if f.db_value in db_values]

    @classmethod
    def from_ai(cls, ai_values):
        return [f.db_value for f in cls if f.ai_value in ai_values]


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
    ALL = ("all", "All Seasons", "year-round")
    SPRING = ("spring", "Spring", "springtime activity")
    SUMMER = ("summer", "Summer", "summer activity")
    FALL = ("fall", "Fall", "autumn activity")
    WINTER = ("winter", "Winter", "winter activity")
    RAINY_DAY = ("rainy_day", "Rainy Day", "rainy day activity")
    SNOWY_DAY = ("snowy_day", "Snowy Day", "snow day activity")


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
    GAMES = ("games", "🎮 Video & Tech Games", "video games or tech-based games")
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
    VOLUNTEERING = ("volunteering", "🤝 Volunteering", "volunteer or community service")
    SPORTS = ("sports", "🏀 Sports", "sports or physical games")
    ZOO_AQUARIUM = (
        "zoo_aquarium",
        "🦁 Zoo / Aquarium",
        "visiting zoo, aquarium, or wildlife park",
    )
