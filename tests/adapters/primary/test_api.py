from fastapi.testclient import TestClient
from src.adapters.primary.api.server import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("src.adapters.primary.api.server.build_graph")
def test_schedule_event_success(mock_build_graph):
    # Mock the graph invoke result
    mock_graph = MagicMock()
    mock_build_graph.return_value = mock_graph
    
    mock_result = {
        "event_summary": {
            "event_id": "test-123",
            "city": "Taipei",
            "datetime_iso": "2025-10-24T14:00:00",
            "duration_min": 60,
            "attendees": ["Alice"],
            "status": "confirmed",
            "reason": "Looks good",
            "notes": "Clear weather"
        }
    }
    mock_graph.invoke.return_value = mock_result

    payload = {"input": "Friday 2pm Taipei meet Alice 60min"}
    response = client.post("/api/schedule", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["result"]["city"] == "Taipei"
    assert data["result"]["attendees"] == ["Alice"]

@patch("src.adapters.primary.api.server.build_graph")
def test_schedule_event_error(mock_build_graph):
    # Mock the graph invoke result with error
    mock_graph = MagicMock()
    mock_build_graph.return_value = mock_graph
    
    mock_result = {
        "error": "Something went wrong"
    }
    mock_graph.invoke.return_value = mock_result

    payload = {"input": "Bad input"}
    response = client.post("/api/schedule", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["error"] == "Something went wrong"
