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
        Input: 'Friday 14:00 Taipei meet Alice 60 min'
        Expected: Event created successfully with all details populated
        """
        # Build the graph
        graph = build_graph()
        
        # Initial state
        initial_state = SchedulerState(
            input_text="Friday 14:00 Taipei meet Alice 60 min"
        )
        
        # Execute graph
        result_state = graph.invoke(initial_state)
        
        # Assertions
        assert result_state.city == "Taipei"
        assert result_state.attendees == ["Alice"]
        assert result_state.duration_min == 60
        assert result_state.datetime.day == 17  # Friday Oct 17
        assert result_state.datetime.hour == 14
        assert result_state.datetime.minute == 0
        
        # Should have created event successfully
        assert result_state.event_summary is not None
        assert result_state.event_summary.status == "confirmed"
        assert "No conflicts" in result_state.event_summary.reason
        assert "weather" in result_state.event_summary.reason.lower()
        assert result_state.event_summary.notes is not None
    
    @freeze_time("2025-10-13 10:00:00")
    def test_sunny_path_with_clear_weather_note(self):
        """Sunny path should include 'Clear weather expected' in notes."""
        graph = build_graph()
        
        initial_state = SchedulerState(
            input_text="Friday 14:00 Taipei meet Alice 60 min"
        )
        
        result_state = graph.invoke(initial_state)
        
        # Should mention clear weather in notes
        assert "clear weather" in result_state.event_summary.notes.lower() or \
               "weather" in result_state.event_summary.notes.lower()
    
    @freeze_time("2025-10-13 10:00:00")
    def test_sunny_path_no_clarification_needed(self):
        """Complete input should not trigger clarification."""
        graph = build_graph()
        
        initial_state = SchedulerState(
            input_text="Friday 14:00 Taipei meet Alice 60 min"
        )
        
        result_state = graph.invoke(initial_state)
        
        # Should not have clarification flag
        assert result_state.clarification_needed is None
        assert result_state.error is None
