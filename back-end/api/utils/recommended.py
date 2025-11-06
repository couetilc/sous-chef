# app/utils/recommended.py

def _lb_to_kg(lb: float) -> float:
    return lb * 0.45359237

def _in_to_cm(inches: float) -> float:
    return inches * 2.54

def mifflin_st_jeor_bmr(sex: str, age: int, height_ft: int, height_in: int, weight_lb: int) -> float:
    height_total_in = (height_ft * 12) + height_in
    height_cm = _in_to_cm(height_total_in)
    weight_kg = _lb_to_kg(weight_lb)
    s = 5 if sex == "male" else -161
    # Mifflin–St Jeor
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + s

def activity_multiplier(level: str) -> float:
    return {
        "low": 1.2,        # sedentary
        "light": 1.375,    # light 1-3x/wk
        "moderate": 1.55,  # moderate 3-5x/wk
        "high": 1.725,     # hard 6-7x/wk
    }.get(level, 1.2)

def calorie_adjust_for_goal(goal: str) -> int:
    # sensible default adjustments (you can tune later or make % based)
    return {
        "lose": -500,
        "maintain": 0,
        "gain": 300,
    }.get(goal, 0)

def protein_grams_per_kg(goal: str) -> float:
    # Slightly higher for cutting, otherwise mid-range evidence-based targets
    return {
        "lose": 2.0,
        "maintain": 1.6,
        "gain": 1.8,
    }.get(goal, 1.6)

def compute_recommendations(health) -> dict:
    """
    health: instance of HealthDetails
    Returns rounded daily calories and protein grams.
    """
    bmr = mifflin_st_jeor_bmr(
        sex=health.sex,
        age=health.age,
        height_ft=health.height_ft,
        height_in=health.height_in,
        weight_lb=health.weight,
    )
    tdee = bmr * activity_multiplier(health.activity_level)
    calories = int(round(tdee + calorie_adjust_for_goal(health.goal)))

    weight_kg = _lb_to_kg(health.weight)
    protein_g = int(round(weight_kg * protein_grams_per_kg(health.goal)))

    # Optional guards (tweak or remove if you like)
    calories = max(calories, 1200)  # prevent unrealistically low numbers
    return {
        "calories_goal": calories,
        "protein_goal_g": protein_g,
        "bmr": int(round(bmr)),
        "tdee": int(round(tdee)),
        "activity_level": health.activity_level,
        "goal": health.goal,
        "sex": health.sex,
        "age": health.age,
        "height": {"ft": health.height_ft, "in": health.height_in},
        "weight_lb": health.weight,
    }
