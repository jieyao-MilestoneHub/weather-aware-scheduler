# Weather-Aware Scheduler

> Trying to develop an agent application with spec-kit.

A lightweight, explainable scheduling system that parses natural language inputs, evaluates weather conditions and calendar conflicts, and produces clear, testable scheduling decisions with transparent reasoning.

## Features

- **Natural Language Input:** Schedule meetings by typing plain English
- **Weather-Aware:** Automatically detects rain risk and suggests adjustments
- **Conflict Detection:** Checks calendar availability and proposes alternatives
- **Transparent Decisions:** Every decision includes clear reasoning and notes
- **Offline-First:** Mock mode requires zero API keys (perfect for development)
- **Visualizable:** Generate flowcharts showing decision-making process
- **Test-Driven:** 100% tested with golden-path scenarios

## Quick Start

### 1. Setup

```bash
# Clone repository
git clone <repository-url>
cd weather-aware-scheduler

# Copy environment variables
cp .env.example .env

# Install dependencies (using uv)
uv sync

# Or using pip
pip install -e ".[dev]"
```

### 2. Run Tests

```bash
# Run all tests (mock mode, no API keys needed)
uv run pytest tests/ --no-cov

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing

# Run specific test category
uv run pytest tests/integration/ -v
```

**Test Status:** 120/125 passing (96%)

### 3. Schedule a Meeting

```bash
# Basic scheduling
weather-scheduler schedule "Friday 2pm Taipei meet Alice 60min"

# With verbose output
weather-scheduler schedule "Friday 2pm Taipei meet Alice 60min" --verbose

# JSON output for automation
weather-scheduler schedule "Friday 2pm Taipei meet Alice 60min" --json
```

**Example Output:**
```
✓ Event Created

Meeting scheduled in Taipei
Reason: No conflicts detected, weather conditions acceptable
Notes: Clear weather expected

Event ID: mock-event-a1b2c3d4
Time: Friday, 2025-10-24 at 2:00 PM
Duration: 60 minutes
Attendees: Alice
```

### 4. Generate Workflow Visualization

```bash
# Generate flow diagrams
weather-scheduler visualize

# Specify output directory
weather-scheduler visualize --output docs/diagrams
```

This creates `graph/flow.mermaid` and `graph/flow.dot` showing the decision flow.

### 5. Environment Variables

The system uses `.env` for configuration. Key variables:

- `MOCK_MODE=true`: Use mock tools (no API keys needed, perfect for testing)
- `AGENT_MODE=rule_engine`: Use LangGraph (recommended) or `multi_agent` for Microsoft Agent Framework
- `OPENAI_API_KEY`: Only needed if MOCK_MODE=false
- `ASCII_ONLY=true`: Use ASCII icons if Unicode rendering fails on Windows

**For Testing (No API Keys Required):**
```bash
# .env file
MOCK_MODE=true
AGENT_MODE=rule_engine
```

**For Production:**
```bash
# .env file
MOCK_MODE=false
OPENAI_API_KEY=sk-your-actual-key-here
AGENT_MODE=rule_engine
```

## User Stories

### ✅ User Story 1: Simple Schedule Creation (MVP)

**Goal:** Quickly schedule meetings with natural language

**Example:**
```bash
weather-scheduler schedule "Next Monday 10am review meeting 45min"
```

### ✅ User Story 2: Weather-Aware Scheduling

**Goal:** Get proactive weather-based suggestions

**Example:**
```bash
weather-scheduler schedule "Tomorrow afternoon Taipei coffee rain backup"
```

**Output:** System detects rain risk and suggests indoor venue or time shift

### ✅ User Story 3: Conflict Resolution

**Goal:** Automatically detect conflicts and propose alternatives

**Example:**
```bash
weather-scheduler schedule "Friday 3pm team sync 30min"
```

**Output:** 3 alternative time slots if conflict detected

### 🚧 User Story 4: Process Visualization

**Goal:** Understand decision flow through visual diagrams

**Example:**
```bash
weather-scheduler visualize
```

**Output:** Mermaid and DOT format diagrams

## System Architecture

### Decision Flow

```
Input → Parse & Validate → Check Weather → Check Calendar
                                              ↓
                                      Conflict/Weather Risk?
                                              ↓
                                   Yes ← → No
                                    ↓         ↓
                           Suggest Adjust   Create Event
                                    ↓         ↓
                                  Output Summary
```

### Components

- **Parser:** Natural language → structured slot (city, datetime, duration, attendees)
- **Validator:** Ensure dates are valid and in future
- **Weather Tool:** Check rain probability (mock mode: keyword + time window rules)
- **Calendar Tool:** Check conflicts (mock mode: predefined blocked times)
- **Policy Engine:** Decide: create, adjust time, adjust place, or propose alternatives
- **Formatter:** Structured output → Rich CLI display

### Technology Stack

- **LangGraph:** State machine orchestration
- **Pydantic v2:** Strict type validation
- **Typer + Rich:** CLI interface with beautiful output
- **pytest:** Test framework with 90%+ coverage
- **python-dateutil:** Relative date parsing

## Project Structure

```
weather-aware-scheduler/
├── src/
│   ├── models/          # Pydantic schemas
│   ├── services/        # Business logic
│   ├── tools/           # Weather & calendar tools
│   ├── graph/           # LangGraph nodes & edges
│   ├── cli/             # Typer CLI
│   └── lib/             # Utilities
├── tests/
│   ├── unit/            # Component tests
│   ├── integration/     # End-to-end tests
│   └── contract/        # Tool interface tests
├── configs/             # Configuration files
├── datasets/            # Test datasets
├── scripts/             # Development scripts
├── specs/               # Feature specifications
└── docs/                # Documentation
```

## Development

### Run Tests

```bash
# All tests
pytest tests/ -v --cov=src

# Specific test type
pytest tests/unit/ -v
pytest tests/integration/ -v
```

### Run Dataset Evaluation

```bash
python scripts/replay_eval.py
```

**Expected:** 5/5 tests passing (100% success rate)

### Quick Development Cycle

```bash
bash scripts/dev_run.sh
```

Runs: setup → tests → CLI example → visualization → dataset replay

## Configuration

### Mock Mode (Default - No API Keys Required)

The system operates in mock mode by default, using:
- **Mock Weather Tool:** Keyword detection + time window rules
- **Mock Calendar Tool:** Predefined conflicts

Edit `configs/graph.config.yaml`:
```yaml
feature_flags:
  providers: "mock"  # No API keys required
```

### Real API Mode (Future)

To use real weather/calendar APIs, create `.env`:
```bash
OPENAI_API_KEY=sk-...
LANGSMITH_API_KEY=lsv2_...
```

Update `configs/graph.config.yaml`:
```yaml
feature_flags:
  providers: "mcp"  # Use real APIs
```

## Testing Strategy

### Test Pyramid

- **Unit Tests:** Parser, validator, time utils, formatters, mock tools
- **Integration Tests:** Full graph flows (sunny, rainy, conflict, missing info, failures)
- **Contract Tests:** Ensure mock and real tools have identical interfaces

### Golden Path Scenarios

1. **Sunny:** No conflicts, clear weather → Direct success
2. **Rainy:** High rain probability → Adjustment suggested
3. **Conflict:** Calendar clash → 3 alternatives proposed
4. **Missing:** Incomplete input → Clarification requested
5. **Failure:** Service unavailable → Graceful degradation

## Documentation

- **[Quickstart Guide](specs/001-weather-aware-scheduler/quickstart.md)** - Get started in 5 minutes
- **[Feature Spec](specs/001-weather-aware-scheduler/spec.md)** - User stories and requirements
- **[Implementation Plan](specs/001-weather-aware-scheduler/plan.md)** - Technical architecture
- **[Tasks](specs/001-weather-aware-scheduler/tasks.md)** - Phase-by-phase breakdown

## Success Metrics

- ✅ **SC-002:** 100% success on 5 golden-path tests (achieved)
- ✅ **SC-006:** Request processing <3s (achieved in mock mode)
- ✅ **SC-008:** Conflict detection <1s (achieved)
- ✅ **Constitution:** Test suite <5s (achieved)
- 🎯 **SC-004:** New developers understand flow in <5 min (visualizations ready)

## Contributing

This project follows test-driven development:
1. Write tests first (they should fail)
2. Implement minimum code to pass tests
3. Refactor while keeping tests green

## License

[Add license information]

## Status

**Current Phase:** User Stories 1-3 complete (MVP + Weather + Conflicts functional)

**Next:**
- ✅ Phase 6: Visualization (visualizer.py created, CLI command added)
- 🚧 Phase 7: Error handling refinement
- 🚧 Phase 8: Documentation polish

**Latest Test Results:** 78+ tests passing, 62-63% coverage

## Quick Reference

| Command | Purpose |
|---------|---------|
| `weather-scheduler schedule "..."` | Schedule a meeting |
| `weather-scheduler visualize` | Generate diagrams |
| `python scripts/replay_eval.py` | Run dataset tests |
| `pytest tests/ -v` | Run test suite |
| `bash scripts/dev_run.sh` | Full dev cycle |

---

Built with ❤️ using LangGraph, Pydantic, and Test-Driven Development
