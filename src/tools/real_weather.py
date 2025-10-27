"""Real weather tool using OpenAI API for weather predictions.

This tool uses OpenAI's LLM to predict weather conditions based on
date, time, and location. In production, this should be replaced with
a real weather API (e.g., OpenWeatherMap, Weather.com API).
"""

import os
from datetime import datetime
from typing import Optional

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.models.entities import WeatherCondition, RiskCategory
from src.tools.base import WeatherTool, WeatherServiceError


class WeatherPredictionInput(BaseModel):
    """Input schema for weather prediction."""
    city: str = Field(description="City name for weather forecast")
    datetime: str = Field(description="ISO format datetime string")
    timezone: str = Field(default="UTC", description="Timezone for the forecast")


class WeatherPredictionOutput(BaseModel):
    """Output schema for weather prediction."""
    condition: str = Field(description="Weather condition (e.g., 'clear', 'rain', 'cloudy')")
    prob_rain: int = Field(description="Probability of rain (0-100%)")
    risk_category: str = Field(description="Risk category: 'low', 'moderate', or 'high'")
    temperature: int = Field(description="Temperature in Celsius")
    description: str = Field(description="Human-readable weather description")


class RealWeatherTool(WeatherTool):
    """Real weather tool using OpenAI API for predictions.

    Note: This uses LLM-based predictions as a placeholder. For production,
    integrate with real weather APIs like OpenWeatherMap or Weather.com.
    """

    def __init__(self):
        """Initialize the real weather tool with OpenAI API."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "sk-...":
            raise ValueError(
                "OPENAI_API_KEY not set in environment. "
                "Please set it in .env file or export it. "
                "Get your key from: https://platform.openai.com/api-keys"
            )

        # Use Azure OpenAI if configured
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if azure_endpoint:
            from langchain_openai import AzureChatOpenAI
            self.llm = AzureChatOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                temperature=0.2,
            )
        else:
            # Use standard OpenAI
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.2,
                api_key=api_key,
            )

        # Create structured output LLM
        self.structured_llm = self.llm.with_structured_output(WeatherPredictionOutput)

    def get_forecast(self, city: str, dt: datetime) -> WeatherCondition:
        """Get weather forecast using OpenAI API.

        Args:
            city: City name
            dt: Target datetime

        Returns:
            WeatherCondition object with forecast data

        Raises:
            WeatherServiceError: If API call fails
        """
        try:
            # Format prompt for weather prediction
            prompt = f"""You are a weather prediction assistant. Predict the weather for:
City: {city}
Date/Time: {dt.strftime('%Y-%m-%d %H:%M')} ({dt.strftime('%A %I:%M %p')})

Provide a realistic weather forecast including:
- Weather condition (clear/rain/cloudy/etc)
- Probability of rain (0-100%)
- Temperature in Celsius
- Risk category (low if <30% rain, moderate if 30-60%, high if >60%)

Consider typical weather patterns for the city and time of day/year."""

            # Call LLM with structured output
            result = self.structured_llm.invoke(prompt)

            # Convert to WeatherCondition
            risk_map = {
                "low": RiskCategory.LOW,
                "moderate": RiskCategory.MODERATE,
                "high": RiskCategory.HIGH,
            }

            return WeatherCondition(
                city=city,
                datetime=dt,
                condition=result.condition,
                prob_rain=result.prob_rain,
                risk_category=risk_map.get(result.risk_category.lower(), RiskCategory.LOW),
                temperature=result.temperature,
                description=result.description,
            )

        except Exception as e:
            raise WeatherServiceError(f"Weather API call failed: {str(e)}")

    def get_weather(self, city: str, dt: datetime) -> dict:
        """Get weather data (alternative interface for compatibility).

        Args:
            city: City name
            dt: Target datetime

        Returns:
            Dictionary with weather data
        """
        forecast = self.get_forecast(city, dt)
        return {
            "city": city,
            "condition": forecast.condition,
            "prob_rain": forecast.prob_rain,
            "temperature": forecast.temperature,
            "description": forecast.description,
        }
