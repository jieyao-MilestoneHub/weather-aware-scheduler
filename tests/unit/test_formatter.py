"""Unit tests for event summary formatting."""
import pytest
from src.services.formatter import format_event_summary
from src.models.outputs import EventSummary


class TestEventSummaryFormatting:
    """Test Rich-formatted output for event summaries."""
    
    def test_confirmed_event_includes_checkmark_icon(self):
        """Confirmed events should include ✓ icon."""
        summary = EventSummary(
            status="confirmed",
            summary_text="Meeting with Alice",
            reason="No conflicts or weather concerns",
            notes="Clear weather expected"
        )
        output = format_event_summary(summary)
        assert "✓" in output
        assert "confirmed" in output.lower() or "created" in output.lower()
    
    def test_adjusted_event_includes_warning_icon(self):
        """Adjusted events should include ⚠ icon."""
        summary = EventSummary(
            status="adjusted",
            summary_text="Meeting with Alice - time shifted",
            reason="High rain probability detected",
            notes="Shifted to 16:00 to avoid rain"
        )
        output = format_event_summary(summary)
        assert "⚠" in output
        assert "adjusted" in output.lower()
    
    def test_error_event_includes_error_icon(self):
        """Error events should include ✗ icon."""
        summary = EventSummary(
            status="error",
            summary_text="Unable to schedule",
            reason="Invalid input format",
            notes="Please provide time and location"
        )
        output = format_event_summary(summary)
        assert "✗" in output
        assert "error" in output.lower() or "unable" in output.lower()
    
    def test_output_includes_all_fields(self):
        """Formatted output should include status, summary, reason, notes."""
        summary = EventSummary(
            status="confirmed",
            summary_text="Meeting with Alice in Taipei",
            reason="No conflicts or weather concerns",
            notes="Duration: 60 minutes"
        )
        output = format_event_summary(summary)
        assert "Meeting with Alice in Taipei" in output
        assert "No conflicts or weather concerns" in output
        assert "Duration: 60 minutes" in output
    
    def test_output_is_non_empty_string(self):
        """format_event_summary should return non-empty string."""
        summary = EventSummary(
            status="confirmed",
            summary_text="Test event",
            reason="Test reason",
            notes="Test notes"
        )
        output = format_event_summary(summary)
        assert isinstance(output, str)
        assert len(output) > 0
