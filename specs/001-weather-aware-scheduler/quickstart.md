# Quickstart Guide: Weather-Aware Scheduler

Get started with the Weather-Aware Scheduler in under 5 minutes!

## Installation

### Prerequisites

- Python 3.11 or higher
- pip or uv package manager

### Install from source

```bash
# Clone the repository
git clone <repository-url>
cd weather-aware-scheduler

# Option 1: Using pip
pip install -e ".[dev]"

# Option 2: Using uv (faster)
uv sync --all-extras
```

### Verify installation

```bash
weather-scheduler version
```

## Basic Usage

The scheduler accepts natural language input and creates structured scheduling decisions.

### Simple scheduling (sunny path)

```bash
weather-scheduler schedule "Friday 2pm Taipei meet Alice 60min"
```

**Expected output:**
```
✓ Event Created

Meeting scheduled in Taipei
Reason: No conflicts detected, weather conditions acceptable
```

### Weather-aware scheduling

```bash
weather-scheduler schedule "Tomorrow afternoon Taipei coffee rain backup"
```

**Expected output:**
```
⚠ Event requires adjustment

Reason: High rain probability detected at requested time
Notes: Consider rescheduling to avoid weather risk
Suggested time: [alternative time]
```

### Conflict detection

```bash
weather-scheduler schedule "Friday 3pm team sync 30min"
```

**Expected output:**
```
⚠ Calendar conflict detected

Reason: Calendar conflict detected at requested time
Notes: Please select from alternative time slots

Alternatives:
1. Friday at 03:30 PM (30 min available)
2. Friday at 04:00 PM (60 min available)
3. Friday at 05:00 PM (90 min available)
```

## Demo Scenarios

### Scenario 1: Clear Weather, No Conflicts

**Input:**
```bash
weather-scheduler schedule "Next Monday 10am review meeting 45min"
```

**What happens:**
- ✓ Parser extracts: Monday, 10:00, 45 minutes
- ✓ Weather check: Clear conditions
- ✓ Calendar check: No conflicts
- ✓ Event created successfully

### Scenario 2: Rain Detection

**Input:**
```bash
weather-scheduler schedule "Friday afternoon park picnic 2 hours rain"
```

**What happens:**
- ⚠️ Parser extracts: Friday, 14:00 (afternoon default), 120 minutes
- ⚠️ Weather check: High rain probability (keyword "rain" detected)
- ⚠️ System suggests: Indoor venue or time shift
- ⚠️ Event adjusted with weather warning

### Scenario 3: Calendar Conflict

**Input:**
```bash
weather-scheduler schedule "Friday 3pm status update 30min"
```

**What happens:**
- ⚠️ Parser extracts: Friday, 15:00, 30 minutes
- ✓ Weather check: Clear conditions
- ⚠️ Calendar check: Conflict detected (pre-configured mock conflict)
- ⚠️ System proposes: 3 alternative time slots

### Scenario 4: Missing Information

**Input:**
```bash
weather-scheduler schedule "Meet Alice tomorrow"
```

**What happens:**
- ❌ Parser extracts: Tomorrow (date), but missing time and location
- ❌ System requests: Clarification with examples
- 💡 User provides: "2pm Taipei 60min"
- ✓ Event created after clarification

## Configuration

### Configuration file

The scheduler uses `configs/graph.config.yaml` for settings:

```yaml
model: "gpt-4o-mini"
temperature: 0.2
timeouts:
  tool: 5s
  node: 15s
retries:
  tool: 2
  llm: 1
thresholds:
  rain_prob: 60  # High rain threshold
feature_flags:
  providers: "mock"  # Use mock tools (no API keys required)
```

### Environment variables

For real API integration (future), create `.env`:

```bash
OPENAI_API_KEY=sk-...
LANGSMITH_API_KEY=lsv2_...
DEFAULT_CITY=Taipei
```

## Visualization

Generate a workflow diagram:

```bash
weather-scheduler visualize
```

This creates:
- `graph/flow.mermaid` - Mermaid format (embeddable in Markdown)
- `graph/flow.dot` - Graphviz DOT format

### Render as SVG

```bash
# Install Graphviz
# On Ubuntu: sudo apt install graphviz
# On Mac: brew install graphviz
# On Windows: Download from https://graphviz.org/download/

# Render DOT file
dot -Tsvg graph/flow.dot -o graph/flow.svg
```

## Troubleshooting

### Issue: "Invalid date/time"

**Problem:** Input date is ambiguous or past

**Solution:** Provide explicit date and time
```bash
# ❌ Bad: "yesterday 2pm"
# ✅ Good: "Friday 2pm" or "2025-10-17 14:00"
```

### Issue: "Missing required fields"

**Problem:** Input is incomplete

**Solution:** Include time, location, and duration
```bash
# ❌ Bad: "meet Alice"
# ✅ Good: "Friday 2pm Taipei meet Alice 60min"
```

### Issue: "Weather service unavailable"

**Problem:** Weather tool error (rare in mock mode)

**Solution:** System degrades gracefully - event still created with note
```
⚠️ Manual weather check recommended
```

### Issue: "No available time slots"

**Problem:** All alternative slots have conflicts or bad weather

**Solution:** Try different time range or manually specify time
```bash
weather-scheduler schedule "Next week Tuesday 10am meeting 30min"
```

## CLI Options

### Verbose mode

See detailed execution steps:
```bash
weather-scheduler schedule "Friday 2pm Taipei meet Alice 60min" --verbose
```

### Help

View all commands and options:
```bash
weather-scheduler --help
weather-scheduler schedule --help
weather-scheduler visualize --help
```

## Development Tools

### Run dataset evaluation

Test against all golden-path scenarios:
```bash
python scripts/replay_eval.py
```

Expected: **5/5 tests passing (100% success rate)**

### Quick development cycle

Run complete dev workflow (setup, test, CLI, visualize):
```bash
bash scripts/dev_run.sh
```

### Run tests

```bash
# All tests
pytest tests/ -v

# Specific test type
pytest tests/unit/ -v        # Unit tests only
pytest tests/integration/ -v # Integration tests only

# With coverage
pytest tests/ -v --cov=src --cov-report=term-missing
```

## Natural Language Input Guide

### Supported date formats

- **Relative:** "tomorrow", "Friday", "next Monday"
- **Absolute:** "2025-10-17", "October 17"

### Supported time formats

- **12-hour:** "2pm", "3:30pm"
- **24-hour:** "14:00", "15:30"
- **Named:** "afternoon" (14:00), "morning" (09:00), "evening" (18:00)

### Duration formats

- **Minutes:** "60min", "90 minutes"
- **Hours:** "1 hour", "2 hours", "1.5 hours"

### Location

- **City names:** "Taipei", "New York", "Tokyo"

### Attendees

- **Single:** "meet Alice"
- **Multiple:** "meet Alice and Bob"

## Next Steps

1. **Try all 4 demo scenarios** to understand system behavior
2. **Generate visualization** to see decision flow
3. **Run dataset evaluation** to verify system health
4. **Read architecture.md** (docs/) for technical details
5. **Check FAQ.md** (docs/) for common questions

## Support

- **Issues:** Report bugs at GitHub Issues
- **Documentation:** See `docs/` folder for architecture details
- **Examples:** Check `datasets/eval_min5.jsonl` for test cases

---

**Quick Reference Card:**

| Command | Purpose |
|---------|---------|
| `weather-scheduler schedule "..."` | Schedule a meeting |
| `weather-scheduler visualize` | Generate workflow diagram |
| `weather-scheduler version` | Show version info |
| `python scripts/replay_eval.py` | Run dataset tests |
| `bash scripts/dev_run.sh` | Full dev cycle |
| `pytest tests/ -v` | Run test suite |

**Default Interpretations:**

| Input | Interpretation |
|-------|---------------|
| "afternoon" | 14:00 (2pm) |
| "morning" | 09:00 (9am) |
| "evening" | 18:00 (6pm) |
| No duration specified | 60 minutes |
| "rain" keyword | High rain probability (70%) |
| Friday 15:00 | Pre-configured conflict (mock) |
