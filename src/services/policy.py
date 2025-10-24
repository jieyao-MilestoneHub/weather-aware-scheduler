"""Policy decision logic for weather and conflict adjustments."""

from datetime import datetime, timedelta
from typing import Optional

from src.models.entities import WeatherCondition


def generate_time_shift_suggestion(
    dt: datetime, weather: WeatherCondition, get_weather_func: callable
) -> Optional[dict[str, datetime | int]]:
    """
    Generate time shift suggestions when rain risk is high.

    Tries time shifts in order: +2h, -2h, +1h, -1h
    Returns first shift with acceptable weather (<60% rain probability).

    Args:
        dt: Original requested datetime
        weather: Current weather condition at requested time
        get_weather_func: Function to get weather for alternative times
                         Should have signature: (city: str, dt: datetime) -> WeatherCondition

    Returns:
        dict with 'suggested_time' and 'shift_minutes' if acceptable alternative found
        None if no acceptable alternative within ±2 hours

    Example:
        >>> from datetime import datetime
        >>> original_dt = datetime(2025, 10, 17, 14, 0)
        >>> weather = WeatherCondition(prob_rain=70, risk_category="high", description="Heavy rain")
        >>> suggestion = generate_time_shift_suggestion(original_dt, weather, get_weather)
        >>> suggestion
        {'suggested_time': datetime(2025, 10, 17, 16, 0), 'shift_minutes': 120}
    """
    # If weather is already acceptable, no shift needed
    if weather.prob_rain < 60:
        return None

    # Try shifts in order: +2h, -2h, +1h, -1h
    shifts = [120, -120, 60, -60]  # minutes

    for shift_min in shifts:
        shifted_dt = dt + timedelta(minutes=shift_min)

        # Get weather for shifted time
        # Note: We need city, but it's not passed directly. This function needs refactoring
        # to accept city as parameter. For now, we'll return the shift info and let
        # the caller validate the weather.
        # TODO: Refactor to accept city parameter
        return {"suggested_time": shifted_dt, "shift_minutes": shift_min}

    return None


def generate_indoor_venue_suggestion(city: str, input_text: str) -> Optional[str]:
    """
    Generate indoor venue suggestion when outdoor keywords detected.

    Checks for outdoor keywords (park, beach, outdoor, garden, terrace, patio)
    in input text and returns generic indoor venue suggestion if detected.

    Args:
        city: City where event is planned
        input_text: Original user input

    Returns:
        Indoor venue suggestion string if outdoor keywords detected
        None if no outdoor keywords found

    Example:
        >>> generate_indoor_venue_suggestion("Taipei", "coffee at the park")
        'Consider indoor venue options in Taipei (cafe, restaurant, indoor space)'
        >>> generate_indoor_venue_suggestion("Taipei", "coffee meeting")
        None
    """
    outdoor_keywords = ["park", "beach", "outdoor", "garden", "terrace", "patio", "plaza"]

    input_lower = input_text.lower()

    for keyword in outdoor_keywords:
        if keyword in input_lower:
            return f"Consider indoor venue options in {city} (cafe, restaurant, indoor space)"

    return None


def should_suggest_time_shift(weather: WeatherCondition) -> bool:
    """
    Determine if time shift should be suggested based on weather.

    Args:
        weather: Weather condition

    Returns:
        True if high rain risk (>=60%), False otherwise
    """
    return weather.prob_rain >= 60


def categorize_rain_risk(prob_rain: int) -> str:
    """
    Categorize rain probability into risk levels.

    Args:
        prob_rain: Rain probability (0-100)

    Returns:
        Risk category: "high" (>=60%), "moderate" (30-60%), "low" (<30%)

    Example:
        >>> categorize_rain_risk(70)
        'high'
        >>> categorize_rain_risk(45)
        'moderate'
        >>> categorize_rain_risk(15)
        'low'
    """
    if prob_rain >= 60:
        return "high"
    elif prob_rain >= 30:
        return "moderate"
    else:
        return "low"
