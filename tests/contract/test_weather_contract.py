"""
Contract tests for WeatherTool interface.

These tests ensure that all WeatherTool implementations (Mock, MCP, etc.) adhere to the same contract:
- Return type: WeatherCondition with required fields
- Exception handling: Raise WeatherServiceError (not generic Exception)
- Field validation: prob_rain (0-100), risk_category (high/moderate/low), description (non-empty)

This allows seamless switching between implementations via feature flags.
"""

import pytest
from datetime import datetime, timezone

from src.tools.base import WeatherTool, WeatherServiceError
from src.tools.mock_weather import MockWeatherTool
from src.models.entities import WeatherCondition


class TestWeatherToolContract:
    """Contract tests that all WeatherTool implementations must pass."""

    @pytest.fixture
    def weather_tool(self) -> WeatherTool:
        """
        Return the WeatherTool implementation to test.

        Currently tests MockWeatherTool. When MCP implementation is added,
        parameterize this fixture to test both implementations.
        """
        return MockWeatherTool()

    def test_get_forecast_returns_weather_condition(self, weather_tool):
        """
        Test that get_forecast returns a WeatherCondition instance.

        Contract requirement: Return value must be WeatherCondition, not dict or other type.
        """
        city = "Taipei"
        dt = datetime(2025, 10, 17, 14, 0, tzinfo=timezone.utc)

        result = weather_tool.get_forecast(city, dt)

        assert isinstance(result, WeatherCondition), \
            f"Expected WeatherCondition, got {type(result).__name__}"

    def test_weather_condition_has_required_fields(self, weather_tool):
        """
        Test that returned WeatherCondition has all required fields with correct types.

        Required fields per contract:
        - prob_rain: int (0-100)
        - risk_category: Literal["high", "moderate", "low"]
        - description: str (non-empty)
        """
        city = "New York"
        dt = datetime(2025, 10, 20, 10, 0, tzinfo=timezone.utc)

        result = weather_tool.get_forecast(city, dt)

        # Check prob_rain field
        assert hasattr(result, 'prob_rain'), "WeatherCondition must have prob_rain field"
        assert isinstance(result.prob_rain, int), f"prob_rain must be int, got {type(result.prob_rain)}"
        assert 0 <= result.prob_rain <= 100, f"prob_rain must be 0-100, got {result.prob_rain}"

        # Check risk_category field
        assert hasattr(result, 'risk_category'), "WeatherCondition must have risk_category field"
        assert result.risk_category in ["high", "moderate", "low"], \
            f"risk_category must be high/moderate/low, got {result.risk_category}"

        # Check description field
        assert hasattr(result, 'description'), "WeatherCondition must have description field"
        assert isinstance(result.description, str), f"description must be str, got {type(result.description)}"
        assert len(result.description) > 0, "description must be non-empty"

    def test_raises_weather_service_error_on_failure(self, weather_tool):
        """
        Test that service failures raise WeatherServiceError, not generic Exception.

        Contract requirement: Must raise specific WeatherServiceError for proper error handling.
        """
        # If tool supports error simulation (like MockWeatherTool with raise_on_error parameter)
        if isinstance(weather_tool, MockWeatherTool):
            tool_with_error = MockWeatherTool(raise_on_error=True)
            city = "Taipei"
            dt = datetime(2025, 10, 17, 14, 0, tzinfo=timezone.utc)

            with pytest.raises(WeatherServiceError) as exc_info:
                tool_with_error.get_forecast(city, dt)

            # Should raise WeatherServiceError specifically, not Exception
            assert isinstance(exc_info.value, WeatherServiceError), \
                "Must raise WeatherServiceError, not generic Exception"

            # Should have descriptive error message
            assert len(str(exc_info.value)) > 0, "Error message should not be empty"

    def test_prob_rain_determines_risk_category_correctly(self, weather_tool):
        """
        Test that risk_category correctly reflects prob_rain thresholds.

        Expected mapping per spec.md FR-007:
        - prob_rain >= 60: "high"
        - 30 <= prob_rain < 60: "moderate"
        - prob_rain < 30: "low"
        """
        city = "Tokyo"
        dt = datetime(2025, 10, 22, 15, 0, tzinfo=timezone.utc)

        result = weather_tool.get_forecast(city, dt)

        # Verify risk_category matches prob_rain
        if result.prob_rain >= 60:
            assert result.risk_category == "high", \
                f"prob_rain {result.prob_rain} should be 'high' risk, got {result.risk_category}"
        elif result.prob_rain >= 30:
            assert result.risk_category == "moderate", \
                f"prob_rain {result.prob_rain} should be 'moderate' risk, got {result.risk_category}"
        else:
            assert result.risk_category == "low", \
                f"prob_rain {result.prob_rain} should be 'low' risk, got {result.risk_category}"

    def test_accepts_string_city_and_datetime(self, weather_tool):
        """
        Test that method accepts required parameter types per contract.

        Signature: get_forecast(city: str, dt: datetime) -> WeatherCondition
        """
        city = "London"
        dt = datetime(2025, 11, 1, 12, 0, tzinfo=timezone.utc)

        # Should not raise TypeError
        result = weather_tool.get_forecast(city, dt)

        assert isinstance(result, WeatherCondition), "Should return WeatherCondition"

    def test_description_provides_context(self, weather_tool):
        """
        Test that description field provides useful context about weather conditions.

        Expected: Non-empty string that describes the weather state or reasoning.
        """
        city = "Paris"
        dt = datetime(2025, 10, 25, 9, 0, tzinfo=timezone.utc)

        result = weather_tool.get_forecast(city, dt)

        # Description should be meaningful (more than just a single word)
        assert len(result.description) >= 5, \
            f"Description should be meaningful, got: {result.description}"

        # Common weather-related keywords should appear
        weather_keywords = ["rain", "clear", "cloud", "sunny", "storm", "dry", "wet", "weather", "sky"]
        description_lower = result.description.lower()
        assert any(keyword in description_lower for keyword in weather_keywords), \
            f"Description should contain weather-related information, got: {result.description}"


@pytest.mark.parametrize("city,dt", [
    ("Taipei", datetime(2025, 10, 17, 14, 0, tzinfo=timezone.utc)),
    ("New York", datetime(2025, 10, 20, 10, 0, tzinfo=timezone.utc)),
    ("London", datetime(2025, 11, 1, 12, 0, tzinfo=timezone.utc)),
])
def test_weather_tool_consistency(city, dt):
    """
    Test that MockWeatherTool produces consistent results for the same inputs.

    Contract requirement: Deterministic behavior for testing.
    """
    tool = MockWeatherTool()

    result1 = tool.get_forecast(city, dt)
    result2 = tool.get_forecast(city, dt)

    # Same inputs should produce same outputs in mock mode
    assert result1.prob_rain == result2.prob_rain, "Should be deterministic"
    assert result1.risk_category == result2.risk_category, "Should be deterministic"
