# Implementation Plan: Weather-Aware Scheduler

**Branch**: `001-weather-aware-scheduler` | **Date**: 2025-10-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-weather-aware-scheduler/spec.md`

## Summary

The Weather-Aware Scheduler is a lightweight, explainable CLI tool that parses natural language scheduling requests, evaluates weather conditions and calendar conflicts using a stateful LangGraph orchestrator, and returns structured, transparent scheduling decisions with clear reasoning. The system operates in mock mode (no API keys required) for v1, with a seamless upgrade path to real MCP providers (Weather/Calendar APIs) via configuration flags.

**Technical Approach**: LangGraph state machine with 6 core nodes (intent_and_slots → check_weather → find_free_slot → confirm_or_adjust → create_event → error_recovery), strict Pydantic v2 schemas for type safety, deterministic mock tools for offline operation, and automated flow visualization (Graphviz/Mermaid) for developer transparency.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: LangGraph (stateful orchestration), Pydantic v2 (strict schemas), Typer (CLI), Rich (console output), python-dateutil (date parsing)
**Storage**: In-memory state for v1 (mock mode); SQLite or JSON file for event persistence (optional extension)
**Testing**: pytest + pytest-cov (unit/integration), hypothesis (property-based date tests)
**Target Platform**: Cross-platform CLI (Windows/Linux/macOS)
**Project Type**: single - CLI application with library-style modules
**Performance Goals**:
- Single schedule request: <3s end-to-end (mock mode)
- Slot extraction + validation: <200ms p95
- Tool calls (mock): <100ms each
- Graph visualization generation: <2s
**Constraints**:
- Zero external API dependencies in v1 (mock mode only)
- Test suite execution: <5s total (per constitution)
- Memory footprint: <100MB for typical workloads
- Support offline operation (no network required)
**Scale/Scope**:
- 5 golden-path test cases (v1 baseline)
- 4 user stories (P1-P4 prioritized)
- 6 graph nodes with 10+ decision edges
- Support 100+ scheduling requests per session

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Gate 1: Design Phase (Planning)

- [x] **Code Quality**:
  - Architecture follows single-responsibility: each node handles one concern (extraction, weather check, conflict check, decision, creation, error)
  - Reusable components identified: SchedulerState (shared), Tool interfaces (mock/MCP adapters), validators (date/time/location)
  - Type safety: Pydantic v2 for all data models and state management
  - Error handling: Explicit error_recovery node with retry logic and graceful degradation

- [x] **Testing Strategy**:
  - Test-first approach: Golden-path tests defined before implementation
  - Coverage targets: 100% for critical paths (slot extraction, weather logic, conflict detection), 90% for business logic, 70% for CLI presentation
  - Test types: Unit (parsers, validators, tools), Integration (graph flows), Contract (tool signatures mock vs MCP)
  - Test hygiene: Deterministic (frozen time, seeded RNG), isolated (no external calls), fast (<5s suite)

- [x] **UX Design**:
  - User flows: 4 prioritized stories with clear acceptance scenarios
  - Error scenarios: 7 edge cases identified with one-shot clarification strategy
  - Response time budgets: <100ms acknowledge, <3s complete request, <5s flow visualization
  - Consistent terminology: "Slot" (extracted data), "Conflict" (time clash), "Adjustment" (weather/time shift)

- [x] **Performance Budget**:
  - Resource constraints: <100MB memory, <50ms CPU blocking (constitution requirement)
  - Performance targets: <3s request (SC-006), <1s conflict detection (SC-008), <200ms slot extraction
  - Monitoring strategy: LangSmith tracing (M2+), pytest benchmarks, manual timing logs in CLI output
  - Optimization: Mock tools return instantly; date parsing cached; graph state immutable copies

### Complexity Justifications

*No constitutional violations identified. All complexity is justified by feature requirements.*

## Project Structure

### Documentation (this feature)

```
specs/001-weather-aware-scheduler/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output (technical research)
├── data-model.md        # Phase 1 output (entity schemas)
├── quickstart.md        # Phase 1 output (user guide)
├── contracts/           # Phase 1 output (tool signatures)
│   ├── weather-tool.md
│   └── calendar-tool.md
└── checklists/
    └── requirements.md  # Spec validation checklist
```

### Source Code (repository root)

```
src/
├── models/                   # Pydantic schemas (Slot, WeatherCondition, CalendarEvent, etc.)
│   ├── __init__.py
│   ├── state.py             # SchedulerState (LangGraph state model)
│   ├── entities.py          # Slot, WeatherCondition, CalendarEvent, Conflict
│   └── outputs.py           # PolicyDecision, EventSummary (structured outputs)
├── services/                # Business logic (parsers, validators, formatters)
│   ├── __init__.py
│   ├── parser.py            # Natural language → Slot extraction
│   ├── validator.py         # Date/time/location validation
│   ├── formatter.py         # EventSummary → CLI output (Rich formatting)
│   └── time_utils.py        # Relative date parsing, timezone handling
├── tools/                   # Mock and MCP tool implementations
│   ├── __init__.py
│   ├── base.py              # WeatherTool, CalendarTool abstract base classes
│   ├── mock_weather.py      # MockWeatherTool (keyword + time window logic)
│   ├── mock_calendar.py     # MockCalendarTool (predefined conflicts)
│   └── mcp_adapters.py      # (M2+) MCP provider wrappers with identical signatures
├── graph/                   # LangGraph orchestration
│   ├── __init__.py
│   ├── nodes.py             # 6 node implementations (intent_and_slots, check_weather, etc.)
│   ├── edges.py             # Conditional routing logic
│   ├── builder.py           # StateGraph construction and compilation
│   └── visualizer.py        # Export to Graphviz/Mermaid
├── cli/                     # Typer CLI entry point
│   ├── __init__.py
│   ├── main.py              # CLI commands (schedule, visualize, test-replay)
│   └── prompts.py           # User-facing messages (error, clarification, confirmation)
└── lib/                     # Shared utilities
    ├── __init__.py
    ├── config.py            # Load graph.config.yaml, .env settings
    ├── retry.py             # Retry decorator with backoff
    └── logging_utils.py     # Structured logging setup

tests/
├── contract/                # Tool signature validation (mock vs MCP compatibility)
│   ├── test_weather_contract.py
│   └── test_calendar_contract.py
├── integration/             # End-to-end graph flows (5 golden paths)
│   ├── test_sunny_path.py
│   ├── test_rainy_adjustment.py
│   ├── test_conflict_resolution.py
│   ├── test_missing_slot.py
│   └── test_service_failure.py
└── unit/                    # Individual component tests
    ├── test_parser.py
    ├── test_validator.py
    ├── test_time_utils.py
    ├── test_mock_tools.py
    └── test_formatter.py

configs/
├── graph.config.yaml        # Model, timeouts, retries, thresholds, feature flags
└── .env.example             # API keys template (for M2+ only)

datasets/
├── eval_min5.jsonl          # 5 golden-path test cases
└── eval_full.jsonl          # (M2+) 20-50 extended cases with i18n/timezone edge cases

scripts/
├── dev_run.sh               # One-command dev loop: setup → run CLI → visualize
├── replay_eval.py           # Load dataset → run graph → report results
└── export_graph.sh          # Generate flow.svg and flow.mermaid

docs/
└── (generated by Phase 1)   # quickstart.md, contracts/, architecture diagrams
```

**Structure Decision**: Selected **single project** structure (Option 1 from plan template). This is a CLI application with library-style modules. No frontend/backend split needed. All code resides in `src/` with clear separation: models (schemas), services (business logic), tools (external integrations), graph (orchestration), cli (user interface), lib (utilities). Tests mirror source structure with contract/integration/unit layers.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

No constitutional violations identified. Architecture adheres to all core principles.

## Phase 0: Research & Technical Validation

**Goal**: Validate technical feasibility of key components and establish baseline implementation patterns.

### Research Areas

1. **LangGraph State Machine Design**
   - Investigate LangGraph `StateGraph` API for defining nodes, edges, and conditional routing
   - Research state persistence strategies (in-memory for v1, extensibility for future SQLite/Redis)
   - Document retry mechanisms: node-level vs tool-level retries
   - Validate graph visualization export: LangGraph's built-in `get_graph()` → Graphviz/Mermaid

2. **Pydantic v2 Structured Output Parsing**
   - Research `model_validate_json()` for strict LLM output parsing
   - Investigate `Field` validators for date/time constraints (e.g., `datetime >= now()`)
   - Document schema evolution strategy for adding optional fields in M2+
   - Validate JSON Schema generation for LLM prompts: `model_json_schema()`

3. **Natural Language Date/Time Parsing**
   - Evaluate `python-dateutil` for relative dates ("Friday", "tomorrow", "next week")
   - Research `dateparser` library for fuzzy parsing (optional, assess necessity)
   - Document custom parsing rules for "afternoon" (14:00), "morning" (09:00), "evening" (18:00)
   - Validate timezone handling: `pytz` vs `zoneinfo` (prefer `zoneinfo` for Python 3.9+)

4. **Mock Tool Design Pattern**
   - Design abstract base classes: `WeatherTool`, `CalendarTool` with `@abstractmethod` signatures
   - Implement deterministic mock logic: keyword matching ("rain") + time window rules
   - Document MCP adapter pattern: identical signatures, feature-flag switching in `graph.config.yaml`
   - Validate tool contract testing: same tests run against mock and MCP implementations

5. **CLI UX with Typer + Rich**
   - Research Typer argument parsing for natural language strings (preserve spaces, quotes)
   - Investigate Rich table formatting for conflict alternatives (3 options with duration)
   - Document progress indicators: `rich.progress.Progress` for operations >500ms
   - Validate error message styling: color codes for ✓ (green), ⚠ (yellow), ✗ (red)

### Research Deliverables

- `specs/001-weather-aware-scheduler/research.md`:
  - LangGraph graph construction code examples
  - Pydantic v2 schema examples with validators
  - Date parsing decision matrix (python-dateutil vs dateparser)
  - Mock tool implementation patterns
  - CLI UX best practices with Rich output examples
  - Performance baseline measurements (initial estimates)

## Phase 1: Design & Contracts

**Goal**: Define all data models, tool contracts, and user-facing documentation before implementation.

### Design Artifacts

1. **Data Model (`data-model.md`)**
   - `SchedulerState`: city, dt, duration_min, attendees, weather, conflicts, proposed, error, clarification_needed
   - `Slot`: city, datetime, duration (minutes), attendees, description
   - `WeatherCondition`: prob_rain (int 0-100), risk_category (high/moderate/low), description
   - `CalendarEvent`: event_id, attendee(s), city, datetime, duration, reason, notes, status
   - `Conflict`: conflicting_event_id, conflicting_time, duration, next_available, candidates (list of 3 datetimes)
   - `PolicyDecision`: action (create/adjust_time/adjust_place/propose_candidates), reason, notes, adjustments (dt_shift_minutes, indoor_hint, candidates)
   - `EventSummary`: status (confirmed/adjusted/conflict/error), summary_text, reason, notes, alternatives (optional)

2. **Tool Contracts (`contracts/`)**

   **`contracts/weather-tool.md`**:
   ```python
   class WeatherTool(ABC):
       @abstractmethod
       def get_forecast(self, city: str, dt: datetime) -> WeatherCondition:
           """
           Returns rain probability and risk category for city at datetime.

           Args:
               city: City name (e.g., "Taipei", "New York")
               dt: Target datetime (timezone-aware)

           Returns:
               WeatherCondition with prob_rain (0-100), risk_category, description

           Raises:
               WeatherServiceError: If service unavailable (triggers retry)
           """
   ```

   **`contracts/calendar-tool.md`**:
   ```python
   class CalendarTool(ABC):
       @abstractmethod
       def find_free_slot(self, dt: datetime, duration_min: int) -> dict:
           """
           Checks if time slot is available; returns conflict info if booked.

           Args:
               dt: Requested datetime
               duration_min: Event duration in minutes

           Returns:
               {
                   "status": "available" | "conflict",
                   "conflict_details": {...},  # if status=conflict
                   "next_available": datetime,  # next free slot
                   "candidates": [datetime, datetime, datetime]  # top 3 options
               }
           """

       @abstractmethod
       def create_event(self, *, city: str, dt: datetime, duration_min: int,
                        attendees: list[str], notes: str | None = None) -> CalendarEvent:
           """
           Creates calendar event and returns confirmation.

           Args:
               city: Location
               dt: Event start time
               duration_min: Duration
               attendees: List of attendee names
               notes: Optional notes (weather warnings, adjustments)

           Returns:
               CalendarEvent with event_id and summary
           """
   ```

3. **Quickstart Guide (`quickstart.md`)**
   - Installation: `pip install -e .` (or `uv sync`)
   - Basic usage: `weather-scheduler schedule "Friday 2pm Taipei meet Alice 60min"`
   - Three demo scenarios:
     1. Sunny day: direct confirmation
     2. Rainy day: adjustment with reason
     3. Conflict: alternative slots
   - Troubleshooting: common errors (invalid date, missing fields, service failure)
   - Configuration: editing `graph.config.yaml` (mock vs MCP toggle)
   - Visualization: `weather-scheduler visualize` → generates `graph/flow.svg`

### Design Validation

- [ ] All Pydantic models have type hints and validators
- [ ] Tool contracts specify exact input/output types (no `Any`)
- [ ] Error scenarios documented with expected behavior
- [ ] Quickstart covers all 4 user stories (P1-P4)
- [ ] Performance budgets allocated per node (<200ms extraction, <100ms tools)

## Phase 2: Core Implementation (Milestone M0-M1)

**Goal**: Build offline-capable mock version with all 6 graph nodes and 5 golden-path tests passing.

### Milestone M0: Foundation (Runs Offline)

**Objective**: Establish project scaffolding, implement mock tools, and create basic graph structure.

#### Tasks

1. **Project Setup**
   - Initialize Python project with `pyproject.toml` (use `uv` for fast lockfile)
   - Configure `ruff` (lint/format), `mypy` (type checking), `pytest` (testing)
   - Setup pre-commit hooks: `ruff format && ruff check && mypy && pytest -q`
   - Create `configs/graph.config.yaml` with defaults (model: "gpt-4o-mini", providers: "mock")

2. **Data Models (`src/models/`)**
   - Implement `SchedulerState` (LangGraph state model) with all fields
   - Implement `Slot`, `WeatherCondition`, `CalendarEvent`, `Conflict`, `PolicyDecision` (Pydantic v2)
   - Add field validators: datetime >= now(), duration 5-480 minutes, prob_rain 0-100
   - Create `EventSummary` for CLI output formatting

3. **Mock Tools (`src/tools/`)**
   - Implement `WeatherTool` and `CalendarTool` abstract base classes
   - Implement `MockWeatherTool`:
     - Keyword detection: "rain" in input → prob_rain=70 (high risk)
     - Time window rules: Friday 14:00-16:00 → prob_rain=65, otherwise prob_rain=15
   - Implement `MockCalendarTool`:
     - Predefined conflicts: Friday 15:00 (30min blocked)
     - `find_free_slot()`: check against conflict list, generate 3 candidates if conflict
     - `create_event()`: return mock event_id and summary

4. **Graph Structure (`src/graph/`)**
   - Create `StateGraph` with 6 nodes: `intent_and_slots`, `check_weather`, `find_free_slot`, `confirm_or_adjust`, `create_event`, `error_recovery`
   - Implement conditional edges:
     - If slot extraction fails → `error_recovery` (slot-filling)
     - If weather high risk → `confirm_or_adjust` (suggest adjustment)
     - If conflict detected → `confirm_or_adjust` (propose alternatives)
     - If all checks pass → `create_event`
   - Compile graph and export visualization: `get_graph().draw_mermaid()` → `graph/flow.mermaid`

5. **CLI Skeleton (`src/cli/main.py`)**
   - Implement `schedule` command: accept natural language string, invoke graph, format output with Rich
   - Implement `visualize` command: export `graph/flow.svg` using Graphviz
   - Add `--verbose` flag for debug logging

**M0 Checkpoint**: CLI runs, mock tools respond, graph structure visible in `flow.svg`

### Milestone M1: Smarter Decisions (Golden-Path Tests Passing)

**Objective**: Implement all node logic, decision policies, and error recovery. Achieve 100% success on 5 golden-path tests.

#### Tasks

1. **Node: intent_and_slots (`src/graph/nodes.py`)**
   - Parse natural language input with structured LLM prompt
   - Extract: city, datetime, duration, attendees using Pydantic schema
   - Validate extracted slot: non-empty city, valid datetime (future), duration 5-480 min
   - If fields missing → set `state.clarification_needed` with specific question
   - Return updated state

2. **Node: check_weather**
   - Call `WeatherTool.get_forecast(city, dt)` with retry (1 attempt, 5s timeout)
   - Store result in `state.weather`
   - Determine `rain_risk`: prob_rain >= 60 → "high", 30-60 → "moderate", <30 → "low"
   - If tool fails → set `state.weather = None`, log warning, continue (graceful degradation)

3. **Node: find_free_slot**
   - Call `CalendarTool.find_free_slot(dt, duration_min)` with retry
   - If conflict → store in `state.conflicts`, extract candidates
   - If available → mark state as `no_conflicts = True`
   - If tool fails → set `state.conflicts = []`, log warning, continue

4. **Node: confirm_or_adjust** (Policy Logic)
   - **High rain risk** (>60%):
     - Generate adjustment options: time shift (±1-2 hours) OR indoor venue suggestion
     - Create `PolicyDecision` with reason="High rain probability detected", notes="Consider indoor venue or shift time"
   - **Moderate rain risk** (30-60%):
     - Create event but add notes="Bring an umbrella - moderate rain chance"
   - **Conflict detected**:
     - Present top 3 candidates from `state.conflicts.candidates`
     - Create `PolicyDecision` with action="propose_candidates", reason="Requested time unavailable"
   - **No issues**:
     - Create `PolicyDecision` with action="create", reason="No conflicts or weather concerns"

5. **Node: create_event**
   - Call `CalendarTool.create_event()` with final slot + notes
   - Generate `EventSummary`: status, summary_text, reason, notes
   - Return summary in state for CLI formatting

6. **Node: error_recovery** (Slot-Filling & Degradation)
   - If `state.clarification_needed`:
     - Generate precise follow-up question (one-shot)
     - Prompt user, parse response, update state
     - Re-run `intent_and_slots` node
   - If tool failures (weather/calendar unavailable):
     - Create `PolicyDecision` with notes="Manual [service] check recommended"
     - Proceed to `create_event` with degraded info
   - If parsing repeatedly fails (>2 attempts):
     - Return error summary: "Unable to parse input - please provide time, location, duration"

7. **Services (`src/services/`)**
   - Implement `parser.py`: regex + `python-dateutil` for relative dates
   - Implement `validator.py`: validate city (non-empty string), datetime (future only), duration (5-480 min)
   - Implement `time_utils.py`: parse "afternoon" (14:00), "morning" (09:00), "Friday" (next Friday from today)
   - Implement `formatter.py`: `EventSummary` → Rich-formatted console output (colored icons, tables)

8. **Testing (`tests/integration/`)**
   - Implement 5 golden-path tests (freeze time with `freezegun`):
     1. `test_sunny_path.py`: "Friday 2pm Taipei meet Alice 60min" → direct success
     2. `test_rainy_adjustment.py`: "Tomorrow afternoon Taipei coffee" (rain detected) → adjustment suggested
     3. `test_conflict_resolution.py`: "Friday 3pm team sync 30min" → conflict → 3 alternatives
     4. `test_missing_slot.py`: "Meet Alice tomorrow" → clarification → complete after response
     5. `test_service_failure.py`: Mock tool raises exception → retry → graceful degradation with notes
   - Assert: 100% success rate, all outputs include reason + notes

**M1 Checkpoint**: All 5 golden tests pass, CLI demos work (sunny/rainy/conflict), outputs include transparency (reason/notes)

## Phase 3: Observability & Testing (Milestone M2)

**Goal**: Add LangSmith tracing, dataset replay script, and MCP adapter foundation.

### Milestone M2: Observability & Regression Testing

#### Tasks

1. **LangSmith Integration**
   - Add LangSmith tracing to graph execution (wrap `StateGraph.invoke()`)
   - Log node transitions, tool calls, and decision points
   - Generate trace URLs in CLI output: "View trace: https://smith.langchain.com/..."
   - Implement trace anonymization: hash attendee names before sending

2. **Dataset & Replay**
   - Create `datasets/eval_min5.jsonl`: 5 golden-path cases in JSONL format
   - Implement `scripts/replay_eval.py`:
     - Load dataset → invoke graph for each case → compare output with expected
     - Calculate success rate (should be 100% for mock mode)
     - Post results to LangSmith as evaluation run
   - Add to CI: `pytest && python scripts/replay_eval.py --ci-mode`

3. **MCP Adapter Foundation**
   - Implement `src/tools/mcp_adapters.py`:
     - `MCPWeatherTool` and `MCPCalendarTool` with identical signatures to mock versions
     - Feature-flag in `graph.config.yaml`: `providers: "mock"` or `providers: "mcp"`
     - Load correct tools in `src/graph/builder.py` based on config
   - Implement contract tests (`tests/contract/`):
     - `test_weather_contract.py`: validate both mock and MCP return `WeatherCondition`
     - `test_calendar_contract.py`: validate both mock and MCP follow same signatures
   - Document MCP setup in `quickstart.md`: API key configuration, provider selection

**M2 Checkpoint**: LangSmith tracing active, dataset replay script runs, MCP adapters ready (contract tests pass)

## Phase 4: Demo-Ready & Documentation (Milestone M3)

**Goal**: Finalize CLI UX, generate all documentation, and prepare demo materials.

### Milestone M3: Demo-Ready

#### Tasks

1. **CLI Polish**
   - Add progress indicators (Rich spinners) for operations >500ms
   - Implement `--json` flag for machine-readable output (scripts/automation)
   - Add `test-replay` command: `weather-scheduler test-replay datasets/eval_min5.jsonl`
   - Improve error messages: include examples of valid input formats

2. **Documentation Generation**
   - Finalize `specs/001-weather-aware-scheduler/quickstart.md`:
     - Installation, basic usage, 4 demo scenarios, troubleshooting, configuration
   - Embed `graph/flow.svg` in README.md with explanation of decision nodes
   - Create `docs/architecture.md`: system overview, node responsibilities, data flow diagram
   - Create FAQ: "How to add a new weather condition?", "How to extend to multi-day events?", "How to switch to real APIs?"

3. **Claude Desktop Integration (Optional)**
   - Create `apps/desktop/prompts.md`: prompt templates for Claude Desktop conversations
   - Document how to invoke scheduler via MCP in Claude Desktop
   - Provide example conversations demonstrating scheduling with reasoning

4. **Performance Validation**
   - Run benchmarks: measure end-to-end latency for all 5 golden paths
   - Validate against success criteria:
     - SC-006: <3s per request (target: ~1-2s with mock tools)
     - SC-008: <1s conflict detection (target: <500ms)
   - Document results in `specs/001-weather-aware-scheduler/performance.md`

**M3 Checkpoint**: CLI demo-ready, documentation complete (quickstart + architecture + FAQ), flow visualization embedded in README

## Phase 5: Future Enhancements (Milestone M4 - Optional)

**Goal**: Advanced features for production readiness (out of v1 scope, documented for future).

### Milestone M4: Nice-to-Have Features

#### Tasks (Future Scope)

1. **RAG-based Venue Suggestions**
   - Create `knowledge/venues.md`: list of indoor venues per city
   - Implement RAG retriever: query venues when high rain risk + city detected
   - Integrate venue suggestions into `confirm_or_adjust` node output

2. **Multi-Model Strategy**
   - Use cheap model (gpt-3.5-turbo) for slot extraction
   - Use advanced model (gpt-4) for ambiguous clarification questions
   - Implement model router in `src/graph/builder.py` based on node complexity

3. **Cost & Latency Dashboard**
   - Log LLM token usage and latency per request
   - Generate daily summary: total tokens, cost estimate, p95 latency
   - Output to CSV: `logs/usage_YYYY-MM-DD.csv`

4. **Extended Dataset**
   - Expand `datasets/eval_full.jsonl` to 20-50 cases
   - Include i18n edge cases: Chinese city names, non-English phrases
   - Include timezone edge cases: cross-timezone meeting requests
   - Target 95% success rate on eval_full

**M4 Checkpoint**: Advanced features implemented (RAG, multi-model, dashboard), extended dataset validated

## Testing Strategy

### Unit Tests (`tests/unit/`)

**Coverage Target**: 90% for business logic (per constitution)

- `test_parser.py`:
  - Test relative date parsing: "Friday" → next Friday, "tomorrow" → today+1
  - Test duration parsing: "60min", "1 hour", "90 minutes" → integer minutes
  - Test attendee extraction: "meet Alice and Bob" → ["Alice", "Bob"]
  - Edge cases: invalid dates (Feb 30), past dates, ambiguous times

- `test_validator.py`:
  - Test datetime validation: future dates pass, past dates fail
  - Test duration validation: 5-480 min pass, 0 or 1000 fail
  - Test city validation: non-empty strings pass, empty/None fail

- `test_time_utils.py`:
  - Test "afternoon" → 14:00, "morning" → 09:00, "evening" → 18:00
  - Test timezone normalization (future: when multi-tz support added)
  - Property-based tests with `hypothesis`: `parse(format(dt)) == dt`

- `test_mock_tools.py`:
  - Test `MockWeatherTool`: "rain" keyword → prob_rain=70
  - Test `MockCalendarTool`: Friday 15:00 → conflict detected, candidates returned
  - Test error cases: tool raises exception → caught and logged

- `test_formatter.py`:
  - Test `EventSummary` → Rich output: includes ✓/⚠/✗ icons
  - Test table formatting for conflict alternatives (3 rows, columns: time/duration)

### Integration Tests (`tests/integration/`)

**Coverage Target**: 100% for critical paths (per constitution)

- `test_sunny_path.py`:
  - Input: "Friday 14:00 Taipei meet Alice 60 min"
  - Expected: Event created, reason="No conflicts or weather concerns", notes="Clear weather expected"

- `test_rainy_adjustment.py`:
  - Input: "Tomorrow afternoon Taipei coffee (rain backup)"
  - Expected: Adjustment suggested, reason="High rain probability detected", notes include time shift or indoor venue

- `test_conflict_resolution.py`:
  - Input: "Friday 3pm team sync 30min" (pre-configured conflict)
  - Expected: 3 alternative slots presented, reason="Requested time unavailable"

- `test_missing_slot.py`:
  - Input: "Meet Alice tomorrow" (missing time/location)
  - Expected: Clarification question asked, after response → event created

- `test_service_failure.py`:
  - Mock tool raises `WeatherServiceError`
  - Expected: Retry once, then graceful degradation with notes="Manual weather check recommended"

### Contract Tests (`tests/contract/`)

**Coverage Target**: 100% for tool interfaces

- `test_weather_contract.py`:
  - Run same test against `MockWeatherTool` and `MCPWeatherTool` (when implemented)
  - Assert: both return `WeatherCondition` with prob_rain, risk_category, description
  - Assert: both raise `WeatherServiceError` on failure (not generic exception)

- `test_calendar_contract.py`:
  - Run same test against `MockCalendarTool` and `MCPCalendarTool`
  - Assert: both return same dict structure for `find_free_slot()`
  - Assert: both return `CalendarEvent` for `create_event()`

### Test Execution

- **Local**: `pytest -v --cov=src --cov-report=term-missing`
- **CI**: GitHub Actions workflow:
  ```yaml
  - name: Lint
    run: ruff check src/ tests/

  - name: Type Check
    run: mypy src/

  - name: Unit Tests
    run: pytest tests/unit/ -v --cov=src --cov-report=xml

  - name: Integration Tests
    run: pytest tests/integration/ -v

  - name: Contract Tests
    run: pytest tests/contract/ -v

  - name: Dataset Replay
    run: python scripts/replay_eval.py --ci-mode
  ```

- **Determinism**: All tests use `freezegun` to freeze time, `random.seed(42)` for reproducibility
- **Performance**: Total test suite <5s (per constitution requirement)

## Deployment & Operations

### Development Workflow

1. **Local Development**
   ```bash
   # One-command setup and run
   ./scripts/dev_run.sh
   # Expands to:
   # - source .env (if exists)
   # - uv sync (install dependencies)
   # - weather-scheduler schedule "Friday 2pm Taipei meet Alice 60min"
   # - weather-scheduler visualize (exports flow.svg)
   # - open latest LangSmith trace (if configured)
   ```

2. **Pre-commit Hooks**
   ```bash
   # Runs automatically on git commit
   ruff format && ruff check && mypy src/ && pytest -q
   ```

3. **Testing Workflow**
   ```bash
   # Run specific test types
   pytest tests/unit/ -v          # Unit tests only
   pytest tests/integration/ -v   # Integration tests only
   pytest tests/ -v --cov=src     # All tests with coverage
   python scripts/replay_eval.py  # Dataset replay (5 golden paths)
   ```

### Configuration Management

**`configs/graph.config.yaml`** (versioned, defaults):
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
  rain_prob: 60  # triggers adjustment
  conflict_window: 30  # minutes buffer for conflict detection
feature_flags:
  providers: "mock"  # "mock" | "mcp"
  enable_tracing: false  # true for M2+
  enable_rag_venues: false  # true for M4
```

**`.env`** (local only, not versioned):
```bash
# Required for M2+ (MCP mode)
OPENAI_API_KEY=sk-...
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=weather-scheduler-dev

# Optional
DEFAULT_CITY=Taipei
```

### Monitoring & Observability (M2+)

- **LangSmith Tracing**: All graph executions traced with node transitions, tool calls, LLM prompts/responses
- **Performance Logging**: CLI outputs execution time: "Completed in 1.23s"
- **Error Tracking**: All exceptions logged to `logs/errors.log` with stack traces
- **Metrics (M4)**: Token usage, cost estimates, latency percentiles exported to CSV

### Security & Privacy

- **No API Keys in v1**: Mock mode requires zero secrets
- **Secret Management (M2+)**: All API keys in `.env` (never committed), loaded via `python-dotenv`
- **PII Protection**: Attendee names NOT stored in logs (hash before LangSmith tracing)
- **Rate Limiting (M2+)**: Respect API rate limits with exponential backoff (handled by retry decorator)

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| LLM fails to extract slot correctly | Medium | High | Pydantic strict parsing + validation; fallback to slot-filling clarification; max 2 attempts before error |
| Mock weather/conflict rules too simplistic | Low | Medium | Document rule logic explicitly; provide override flag `--force-create` to bypass checks |
| Graph visualization too complex for new users | Medium | Medium | Include legend in `flow.svg`; label all edges with conditions; test with 3+ new developers (target: understand in <5 min) |
| Date parsing fails for edge cases (leap years, DST) | Low | Medium | Use battle-tested `python-dateutil`; add property-based tests with `hypothesis`; validate with 50+ date samples |
| Test suite exceeds 5s limit | Low | High (constitutional violation) | Use fast test fixtures; avoid real LLM calls in unit tests (mock all LLM responses); parallelize test execution with `pytest-xdist` if needed |
| Real API integration (M2+) breaks contract | Medium | High | Contract tests enforce identical signatures; adapter pattern isolates integration; feature-flag allows quick rollback to mock mode |

## Success Metrics & Validation

### Definition of Done (v1)

- [x] Three CLI test cases work without API keys:
  1. Sunny: `weather-scheduler schedule "Friday 2pm Taipei meet Alice 60min"` → ✓ Event Created
  2. Rainy: `weather-scheduler schedule "Tomorrow afternoon Taipei coffee rain backup"` → ⚠ Schedule Adjusted
  3. Conflict: `weather-scheduler schedule "Friday 3pm team sync 30min"` → ⚠ 3 alternatives presented
- [x] Process flowchart: `weather-scheduler visualize` → generates `graph/flow.svg` + `flow.mermaid`
- [x] All 5 golden regression tests pass: `python scripts/replay_eval.py` → 5/5 success (100%)
- [x] Each output includes reason + notes: All `EventSummary` objects populated
- [x] Clarification at most once: `error_recovery` node asks one question, then fails if still unclear
- [x] User-friendly errors: All error messages actionable (e.g., "Please provide time in format: 2pm or 14:00")

### Performance Validation

| Metric | Target | Measurement Method | Status |
|--------|--------|-------------------|--------|
| SC-006: Request latency | <3s | `pytest tests/integration/ --durations=5` | TBD (M1) |
| SC-008: Conflict detection | <1s | Time `find_free_slot` node execution | TBD (M1) |
| Constitution: Test suite | <5s | `pytest tests/ --durations=0` | TBD (M1) |
| Constitution: Memory | <500MB | `memory_profiler` on graph execution | TBD (M1) |

### Quality Gates (Pre-Release)

- [ ] **Gate 1 (Design)**: Constitution check passed (above)
- [ ] **Gate 2 (Implementation)**:
  - All tests pass (`pytest tests/ -v`)
  - Coverage ≥90% business logic (`pytest --cov=src --cov-report=term`)
  - Type checking passes (`mypy src/`)
  - Linting passes (`ruff check src/ tests/`)
- [ ] **Gate 3 (Release)**:
  - 5 golden paths 100% success (dataset replay)
  - Documentation complete (quickstart + architecture + FAQ)
  - Flow visualization embedded in README
  - CLI demo video recorded (optional, 2-3 minutes)

## Appendix: Key Decision Log

### Why LangGraph over LangChain LCEL?

- **State Management**: LangGraph provides built-in state persistence and branching, crucial for error recovery and slot-filling flows
- **Visualization**: Native `get_graph().draw_mermaid()` support aligns with FR-023 (flow visualization requirement)
- **Observability**: LangSmith integration more mature for graph-based workflows

### Why Pydantic v2 over dataclasses?

- **Validation**: Built-in field validators (e.g., `Field(gt=0, lt=480)` for duration) reduce boilerplate
- **JSON Schema**: `model_json_schema()` generates schemas for LLM structured outputs automatically
- **Performance**: v2 Rust core significantly faster for large-scale parsing (future-proofing)

### Why Mock Mode First?

- **Offline Development**: No API keys required → faster onboarding, CI/CD without secrets management
- **Deterministic Testing**: Mock tools return predictable data → reproducible tests, easier debugging
- **Cost Control**: Zero LLM/API costs during development → iterate rapidly without budget concerns

### Why Single Project Structure?

- **Simplicity**: No frontend/backend split needed for CLI application
- **Fast Iteration**: All code in one repo → easier refactoring, no cross-repo coordination
- **Constitutional Compliance**: Aligns with "Simplicity" principle (minimize unnecessary complexity)

---

**Next Steps**:
1. Review and approve this plan
2. Run `/speckit.tasks` to generate phase-by-phase task breakdown
3. Begin Phase 0 research (validate LangGraph, Pydantic v2, date parsing)
