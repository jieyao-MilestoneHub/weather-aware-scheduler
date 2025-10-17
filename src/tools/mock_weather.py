"""Mock weather tool with deterministic rules for testing."""

from datetime import datetime as dt_type

from src.models.entities import RiskCategory, WeatherCondition
from src.tools.base import WeatherTool, WeatherServiceError


class MockWeatherTool(WeatherTool):
    """Mock weather tool using keyword detection and time window rules.

    Deterministic logic for offline testing:
    1. Keyword detection: "rain" in context → prob_rain=70 (high risk)
    2. Time window rules: Friday 14:00-16:00 → prob_rain=65 (high risk)
    3. Default: prob_rain=15 (low risk)
    """

    def __init__(self, *, raise_on_error: bool = False, context: str = ""):
        """Initialize mock weather tool.

        Args:
            raise_on_error: If True, raise WeatherServiceError for testing
            context: Additional context for keyword detection (e.g., user input)
        """
        self.raise_on_error = raise_on_error
        self.context = context.lower()

    def get_forecast(self, city: str, dt: dt_type) -> WeatherCondition:
        """Get mock weather forecast based on deterministic rules.

        Args:
            city: City name (not used in mock logic)
            dt: Target datetime

        Returns:
            WeatherCondition with prob_rain and auto-categorized risk

        Raises:
            WeatherServiceError: If raise_on_error=True
        """
        if self.raise_on_error:
            raise WeatherServiceError("Mock weather service unavailable")

        # Rule 1: Keyword detection
        if "rain" in self.context or "rainy" in self.context:
            prob_rain = 70
            description = f"High chance of rain detected in {city} for {dt.strftime('%A %H:%M')}"
            # Risk category auto-computed by WeatherCondition validator
            return WeatherCondition(
                prob_rain=prob_rain,
                risk_category=RiskCategory.HIGH,
                description=description
            )

        # Rule 2: Time window - Friday 14:00-16:00 (high rain probability window)
        if dt.weekday() == 4:  # Friday
            if 14 <= dt.hour < 16:
                prob_rain = 65
                description = f"Typical rainy period in {city} on Friday afternoon"
                return WeatherCondition(
                    prob_rain=prob_rain,
                    risk_category=RiskCategory.HIGH,
                    description=description
                )

        # Rule 3: Default - low rain probability
        prob_rain = 15
        description = f"Clear weather expected in {city} for {dt.strftime('%A %H:%M')}"
        return WeatherCondition(
            prob_rain=prob_rain,
            risk_category=RiskCategory.LOW,
            description=description
        )
