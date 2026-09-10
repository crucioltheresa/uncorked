from products.models import Wine

QUESTIONS = [
    {
        "id": "type",
        "text": "What type of wine are you in the mood for?",
        "options": [
            {"value": "red", "label": "Red 🍷"},
            {"value": "white", "label": "White 🥂"},
            {"value": "sparkling", "label": "Sparkling 🫧"},
            {"value": "orange", "label": "Orange 🍊"},
            {"value": "rose", "label": "Rosé 🌸"},
            {"value": "surprise", "label": "Surprise me 🎲"},
        ],
    },
    {
        "id": "occasion",
        "text": "What's the occasion?",
        "options": [
            {"value": "casual", "label": "Casual night in 🛋️"},
            {"value": "dinner", "label": "Dinner party 🍽️"},
            {"value": "romantic", "label": "Romantic evening 🕯️"},
            {"value": "celebration", "label": "Celebration 🥂"},
        ],
    },
    {
        "id": "food",
        "text": "Any food involved?",
        "options": [
            {"value": "cheese", "label": "Cheese 🧀"},
            {"value": "seafood", "label": "Seafood 🐟"},
            {"value": "meat", "label": "Red meat 🥩"},
            {"value": "vegetarian", "label": "Vegetarian 🌿"},
            {"value": "none", "label": "Just drinking 🍷"},
        ],
    },
    {
        "id": "style",
        "text": "What style do you prefer?",
        "options": [
            {"value": "light", "label": "Light & delicate"},
            {"value": "bold", "label": "Bold & rich"},
            {"value": "funky", "label": "Funky & natural"},
            {"value": "unusual", "label": "Something unusual"},
        ],
    },
    {
        "id": "budget",
        "text": "What's your budget?",
        "options": [
            {"value": "under20", "label": "Under €20"},
            {"value": "20to35", "label": "€20 – €35"},
            {"value": "35plus", "label": "€35+"},
        ],
    },
]


def score_wine(wine, answers):
    score = 0

    # Type match
    wine_type = answers.get("type")
    if wine_type == "surprise":
        score += 1
    elif wine.wine_type == wine_type:
        score += 3

    # Food pairing
    food = answers.get("food", "")
    if food and food != "none":
        if food.lower() in wine.food_pairing.lower():
            score += 2

    # Style match via character field
    style = answers.get("style", "")
    style_keywords = {
        "light": ["delicate", "pale", "light", "fresh", "crisp"],
        "bold": ["bold", "rich", "full", "robust", "structured"],
        "funky": ["funky", "natural", "textured", "wild", "cloudy"],
        "unusual": ["unusual", "unique", "rare", "unexpected", "experimental"],
    }
    for kw in style_keywords.get(style, []):
        if kw in wine.character.lower():
            score += 2
            break

    # Budget filter — eliminatory
    try:
        price = float(wine.price)
    except (ValueError, TypeError):
        return 0

    budget = answers.get("budget", "")
    if budget == "under20" and price <= 20:
        score += 1
    elif budget == "20to35" and 20 < price <= 35:
        score += 1
    elif budget == "35plus" and price > 35:
        score += 1
    else:
        return 0  # out of budget — eliminated

    return score


def get_recommendations(answers):
    wines = Wine.objects.filter(is_available=True)
    scored = []

    for wine in wines:
        s = score_wine(wine, answers)
        if s > 0:
            scored.append((wine, s))

    scored.sort(key=lambda x: x[1], reverse=True)

    # If surprise me — shuffle top results
    if answers.get("type") == "surprise":
        import random

        top = scored[:10]
        random.shuffle(top)
        return [w for w, s in top[:3]]

    return [w for w, s in scored[:3]]
