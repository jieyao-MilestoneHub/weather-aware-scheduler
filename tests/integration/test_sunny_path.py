"""Integration test for sunny path - simple schedule creation with no issues."""
import pytest
from datetime import datetime
from freezegun import freeze_time
from src.graph.builder import build_graph
from src.models.state import SchedulerState


class TestSunnyPathIntegration:
    """End-to-end test for successful scheduling with no weather/conflict issues."""
    
    @freeze_time("2025-10-13 10:00:00")  # Monday morning
    def test_full_sunny_path_execution(self):
        """
        Input: 'Friday 10:00 Taipei meet Alice 60 min'
        Expected: Event created successfully with all details populated
        Note: Friday 10:00 avoids the 14:00-16:00 rainy window in mock weather
        """
        # Build the graph
        graph = build_graph()

        # Initial state - using Friday 10:00 to avoid rainy window
        initial_state = SchedulerState(
            input_text="Friday 10:00 Taipei meet Alice 60 min"
        )

        # Execute graph (returns dict, not SchedulerState object)
        result_state = graph.invoke(initial_state)

        # Assertions - access via dict keys
        assert result_state["city"] == "Taipei"
        assert result_state["attendees"] == ["Alice"]
        assert result_state["duration_min"] == 60
        assert result_state["dt"].day == 17  # Friday Oct 17
        assert result_state["dt"].hour == 10
        assert result_state["dt"].minute == 0

        # Should have created event successfully
        assert result_state["event_summary"] is not None
        assert result_state["event_summary"]["status"] == "confirmed"
        assert "No conflicts" in result_state["event_summary"]["reason"]
        assert "weather" in result_state["event_summary"]["reason"].lower()
        # Notes may be None for sunny path (no special warnings needed)
        # Just verify event_summary structure is complete
    
    @freeze_time("2025-10-13 10:00:00")
    def test_sunny_path_with_clear_weather_note(self):
        """Sunny path should have acceptable weather in reason."""
        graph = build_graph()

        initial_state = SchedulerState(
            input_text="Friday 10:00 Taipei meet Alice 60 min"  # Avoid rainy window
        )

        result_state = graph.invoke(initial_state)

        # Should mention acceptable weather in reason (notes may be None for sunny path)
        assert result_state["event_summary"] is not None
        assert result_state["event_summary"]["status"] == "confirmed"
        # Weather mention should be in reason if not in notes
        if result_state["event_summary"]["notes"]:
            assert "weather" in result_state["event_summary"]["notes"].lower()
        else:
            assert "weather" in result_state["event_summary"]["reason"].lower()
    
    @freeze_time("2025-10-13 10:00:00")
    def test_sunny_path_no_clarification_needed(self):
        """Complete input should not trigger clarification."""
        graph = build_graph()

        initial_state = SchedulerState(
            input_text="Friday 10:00 Taipei meet Alice 60 min"  # Avoid rainy window
        )
        
        result_state = graph.invoke(initial_state)

        # Should not have clarification flag (access via dict keys)
        assert result_state.get("clarification_needed") is None
        assert result_state.get("error") is None
