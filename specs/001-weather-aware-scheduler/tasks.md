# Tasks: Weather-Aware Scheduler

**Input**: Design documents from `/specs/001-weather-aware-scheduler/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are REQUIRED per spec (FR-027 through FR-030) and constitution (TDD mandatory). Test-first approach enforced: tests written before implementation, tests MUST fail initially.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root
- Paths assume single project structure (per plan.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure: initialize directories `src/`, `tests/`, `configs/`, `datasets/`, `scripts/`, `docs/` per plan.md structure
- [x] T002 Initialize Python project with `pyproject.toml` using uv/poetry with dependencies: langgraph, pydantic>=2.0, typer, rich, python-dateutil, pytest, pytest-cov, freezegun, hypothesis, ruff, mypy
- [x] T003 [P] Configure ruff for linting and formatting in `pyproject.toml`: line-length=100, target-version="py311"
- [x] T004 [P] Configure mypy for type checking in `pyproject.toml`: strict=true, python_version="3.11"
- [x] T005 [P] Configure pytest in `pyproject.toml`: testpaths=["tests"], addopts="--cov=src --cov-report=term-missing"
- [x] T006 [P] Setup pre-commit hooks: create `.pre-commit-config.yaml` with ruff format, ruff check, mypy, pytest -q
- [x] T007 [P] Create `configs/graph.config.yaml` with defaults: model="gpt-4o-mini", temperature=0.2, timeouts(tool=5s, node=15s), retries(tool=2, llm=1, retry_delay_seconds=2), thresholds(rain_prob=60), feature_flags(providers="mock") (addresses analysis finding U2)
- [x] T008 [P] Create `configs/.env.example` with placeholders: OPENAI_API_KEY, LANGSMITH_API_KEY, LANGSMITH_PROJECT, DEFAULT_CITY
- [x] T009 [P] Create `.gitignore`: include `.env`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.coverage`, `.mypy_cache/`, `*.egg-info/`, `dist/`, `build/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Shared Data Models

- [x] T010 [P] Create `src/models/__init__.py` with exports for all model classes
- [x] T011 [P] Create `src/models/state.py`: implement SchedulerState (LangGraph state model) with fields: city (str|None), dt (datetime|None), duration_min (int|None), attendees (list[str]), description (str|None), weather (dict|None), conflicts (list), proposed (list), error (str|None), clarification_needed (str|None), no_conflicts (bool) (addresses analysis finding I1)
- [x] T012 [P] Create `src/models/entities.py`: implement Slot (city, datetime, duration, attendees, description), WeatherCondition (prob_rain 0-100, risk_category enum, description), CalendarEvent (event_id, attendees, city, datetime, duration, reason, notes, status), Conflict (conflicting_event_id, conflicting_time, duration, next_available, candidates list)
- [x] T013 [P] Create `src/models/outputs.py`: implement PolicyDecision (action enum, reason, notes, adjustments dict), EventSummary (status enum, summary_text, reason, notes, alternatives optional)
- [x] T014 Add Pydantic v2 field validators to entities.py: datetime>=now(), duration 5-480 minutes, prob_rain 0-100, non-empty city strings

### Tool Interfaces & Mock Implementations

- [x] T015 [P] Create `src/tools/__init__.py` with exports for tool classes
- [x] T016 [P] Create `src/tools/base.py`: define WeatherTool abstract base class with @abstractmethod get_forecast(city: str, dt: datetime) -> WeatherCondition
- [x] T017 Create `src/tools/base.py`: define CalendarTool abstract base class with @abstractmethod find_free_slot(dt: datetime, duration_min: int) -> dict and @abstractmethod create_event(**kwargs) -> CalendarEvent (same file, depends on T016)
- [x] T018 Create `src/tools/mock_weather.py`: implement MockWeatherTool(WeatherTool) with keyword detection ("rain" → prob_rain=70) and time window rules (Friday 14:00-16:00 → prob_rain=65, else prob_rain=15)
- [x] T019 Create `src/tools/mock_calendar.py`: implement MockCalendarTool(CalendarTool) with predefined conflicts (Friday 15:00 30min blocked), find_free_slot() checks conflicts and generates 3 candidates, create_event() returns mock event_id and summary

### Shared Services & Utilities

- [x] T020 [P] Create `src/services/__init__.py` with exports for service functions
- [x] T021 [P] Create `src/lib/__init__.py` with exports for utility functions
- [x] T022 [P] Create `src/lib/config.py`: implement load_config() to read graph.config.yaml and .env using python-dotenv and pyyaml
- [x] T023 [P] Create `src/lib/retry.py`: implement @retry decorator with exponential backoff, configurable max_attempts and timeout
- [x] T024 [P] Create `src/lib/logging_utils.py`: setup structured logging with log levels, file handlers (logs/errors.log), and console output

### Graph Foundation

- [x] T025 [P] Create `src/graph/__init__.py` with exports for graph components
- [x] T026 Create `src/graph/builder.py`: implement build_graph() function that constructs StateGraph with 6 node placeholders (intent_and_slots, check_weather, find_free_slot, confirm_or_adjust, create_event, error_recovery) and basic conditional edges, returns compiled graph

**Checkpoint**: Foundation ready - all shared infrastructure in place, tools and models available, graph structure defined

---

## Phase 3: User Story 1 - Simple Schedule Creation (Priority: P1) 🎯 MVP

**Goal**: Enable users to schedule meetings via natural language input and receive confirmed events with structured output

**Independent Test**: Input "Friday 14:00 Taipei meet Alice 60 min" → verify structured schedule returned with all details (time, location, attendee, duration)

### Tests for User Story 1 (Test-First - MUST write and fail before implementation)

- [ ] T027 [P] [US1] Create `tests/unit/__init__.py` empty file
- [ ] T028 [P] [US1] Create `tests/integration/__init__.py` empty file
- [ ] T029 [P] [US1] Create `tests/unit/test_parser.py`: test relative date parsing ("Friday" → next Friday, "tomorrow" → today+1), test duration parsing ("60min", "1 hour" → 60), test attendee extraction ("meet Alice and Bob" → ["Alice", "Bob"]), edge cases (invalid dates, past dates)
- [ ] T030 [P] [US1] Create `tests/unit/test_validator.py`: test datetime validation (future dates pass, past dates fail), test duration validation (5-480 min pass, 0/1000 fail), test city validation (non-empty pass, empty/None fail)
- [ ] T031 [P] [US1] Create `tests/unit/test_time_utils.py`: test "afternoon"→14:00, "morning"→09:00, "evening"→18:00, property-based tests with hypothesis (parse(format(dt))==dt)
- [ ] T032 [P] [US1] Create `tests/unit/test_formatter.py`: test EventSummary → Rich output includes ✓/⚠/✗ icons, test formatting for confirmed events with all fields populated
- [ ] T033 [US1] Create `tests/integration/test_sunny_path.py`: test input "Friday 14:00 Taipei meet Alice 60 min" → expect event created, reason="No conflicts or weather concerns", notes="Clear weather expected", use freezegun to freeze time, verify full end-to-end graph execution

**RUN TESTS - ALL SHOULD FAIL (Red phase of TDD)**

### Implementation for User Story 1

- [ ] T034 [P] [US1] Create `src/services/parser.py`: implement parse_natural_language(input: str) -> Slot with regex + python-dateutil for relative dates, extract city/datetime/duration/attendees, return Slot or raise ParseError
- [ ] T035 [P] [US1] Create `src/services/validator.py`: implement validate_slot(slot: Slot) -> bool with checks: non-empty city, datetime in future, duration 5-480 min, raise ValidationError with specific message
- [ ] T036 [P] [US1] Create `src/services/time_utils.py`: implement parse_relative_time(text: str) -> datetime with mappings ("afternoon"→14:00, "morning"→09:00, "Friday"→next Friday), handle timezone with zoneinfo
- [ ] T037 [P] [US1] Create `src/services/formatter.py`: implement format_event_summary(summary: EventSummary) -> str with Rich formatting (colored icons ✓/⚠/✗, tables, structured output)
- [ ] T038 [US1] Implement `src/graph/nodes.py`: create intent_and_slots_node(state: SchedulerState) -> SchedulerState that calls parse_natural_language(), validates with validate_slot(), updates state with extracted slot or sets clarification_needed, returns updated state
- [ ] T039 [US1] Implement `src/graph/nodes.py`: create create_event_node(state: SchedulerState) -> SchedulerState that calls CalendarTool.create_event() with state slot data, generates EventSummary with status/reason/notes, returns state with summary (same file as T038)
- [ ] T040 [US1] Implement `src/graph/edges.py`: create conditional_edge_from_intent(state: SchedulerState) -> str that routes to "check_weather" if slot valid, "error_recovery" if clarification_needed
- [ ] T041 [US1] Update `src/graph/builder.py`: wire intent_and_slots_node and create_event_node into graph with proper edges, ensure sunny path (no weather/conflict concerns) flows: intent_and_slots → check_weather → find_free_slot → confirm_or_adjust → create_event
- [ ] T042 [P] [US1] Create `src/cli/__init__.py` empty file
- [ ] T043 [US1] Create `src/cli/main.py`: implement Typer CLI app with schedule(input: str) command that loads config, builds graph, invokes graph with input, formats output with Rich, handles errors gracefully
- [ ] T044 [US1] Create `src/cli/prompts.py`: define user-facing message templates for success, error, clarification (strings only, imported by main.py)

**RUN TESTS - ALL SHOULD PASS (Green phase of TDD)**

### Refactoring & Polish for User Story 1

- [ ] T045 [US1] Refactor parser.py: extract common regex patterns to module-level constants, add type hints to all functions, add docstrings with examples
- [ ] T046 [US1] Refactor nodes.py: ensure single-responsibility per node (max 50 lines per function), extract helper functions if needed, add comprehensive error handling
- [ ] T047 [US1] Add integration test for partial input: test "meet Alice Friday" → clarification asked for time/location, verify one-shot clarification strategy works

**Checkpoint**: User Story 1 complete and independently testable - users can create simple schedules with natural language, all tests pass

---

## Phase 4: User Story 2 - Weather-Aware Scheduling (Priority: P2)

**Goal**: System considers weather conditions when scheduling and provides proactive suggestions for adjustments

**Independent Test**: Input "Tomorrow afternoon Taipei coffee (rain backup)" → verify rain detected, adjustment suggested with reasoning

### Tests for User Story 2 (Test-First)

- [ ] T048 [P] [US2] Create `tests/unit/test_mock_tools.py`: test MockWeatherTool with "rain" keyword → prob_rain=70, test time window Friday 14:00-16:00 → prob_rain=65, test error cases (tool raises exception → caught)
- [ ] T049 [US2] Create `tests/integration/test_rainy_adjustment.py`: test input "Tomorrow afternoon Taipei coffee rain backup" with mock weather returning high rain probability → expect adjustment suggested, reason="High rain probability detected", notes include time shift or indoor venue, use freezegun

**RUN TESTS - SHOULD FAIL**

### Implementation for User Story 2

- [ ] T050 [US2] Implement `src/graph/nodes.py`: create check_weather_node(state: SchedulerState) -> SchedulerState that calls WeatherTool.get_forecast(city, dt) with retry decorator, stores result in state.weather, determines rain_risk (>=60 "high", 30-60 "moderate", <30 "low"), gracefully degrades if tool fails (set weather=None, log warning) (same file as T038)
- [ ] T051 [US2] Implement `src/graph/nodes.py`: create confirm_or_adjust_node(state: SchedulerState) -> SchedulerState with policy logic: if high rain risk (>60%) generate time shift ±1-2h or indoor venue suggestion, if moderate rain (30-60%) add notes "Bring umbrella", if no issues create PolicyDecision with action="create", return state with decision (same file as T038)
- [ ] T051a [US2] Create `src/services/policy.py`: implement generate_time_shift_suggestion(dt: datetime, weather: WeatherCondition) -> dict that tries time shifts in order: +2h, -2h, +1h, -1h, returns first shift with acceptable weather (<60% rain); implement generate_indoor_venue_suggestion(city: str, input_text: str) -> str that checks for outdoor keywords (park, beach, outdoor) in input and returns generic indoor venue suggestion if detected (addresses analysis finding C1)
- [ ] T052 [US2] Implement `src/graph/edges.py`: create conditional_edge_from_weather(state: SchedulerState) -> str that routes to "find_free_slot" after weather check regardless of result (graceful degradation) (same file as T040)
- [ ] T053 [US2] Update `src/graph/builder.py`: wire check_weather_node and confirm_or_adjust_node into graph, ensure weather check happens after intent_and_slots and before conflict check
- [ ] T054 [US2] Update `src/services/formatter.py`: add formatting for weather-adjusted events with ⚠ icon, display original time vs adjusted time, include weather reasoning and notes prominently

**RUN TESTS - SHOULD PASS**

### Refactoring for User Story 2

- [ ] T055 [US2] Refactor check_weather_node: extract rain_risk categorization logic to separate function, add unit test for categorization (prob_rain → risk_category)
- [ ] T056 [US2] Refactor confirm_or_adjust_node: extract policy logic to separate policy.py module with functions: should_suggest_time_shift(), generate_indoor_venue_note(), keep node thin (orchestration only)

**Checkpoint**: User Story 2 complete - weather-aware scheduling works, adjustments include clear reasoning, tests pass

---

## Phase 5: User Story 3 - Conflict Resolution (Priority: P3)

**Goal**: Automatic detection and resolution of scheduling conflicts with alternative slot proposals

**Independent Test**: Input "Friday 3pm team sync 30min" (pre-configured conflict) → verify conflict detected, 3 alternative slots proposed

### Tests for User Story 3 (Test-First)

- [ ] T057 [US2] Create `tests/unit/test_mock_tools.py`: add tests for MockCalendarTool: Friday 15:00 → conflict detected, 3 candidates returned, test find_free_slot() with various durations (15min, 60min, 120min), test create_event() returns event_id and summary (same file as T048)
- [ ] T058 [US3] Create `tests/integration/test_conflict_resolution.py`: test input "Friday 3pm team sync 30min" with mock calendar showing conflict → expect 3 alternative slots presented (15:30, 16:00, 17:00), reason="Requested time unavailable", use freezegun

**RUN TESTS - SHOULD FAIL**

### Implementation for User Story 3

- [ ] T059 [US3] Implement `src/graph/nodes.py`: create find_free_slot_node(state: SchedulerState) -> SchedulerState that calls CalendarTool.find_free_slot(dt, duration_min) with retry, if conflict stores in state.conflicts with candidates, if available sets no_conflicts=True, gracefully degrades if tool fails (same file as T038)
- [ ] T060 [US3] Update `src/graph/nodes.py`: enhance confirm_or_adjust_node to handle conflicts: if state.conflicts present, create PolicyDecision with action="propose_candidates", extract top 3 from state.conflicts.candidates, include duration info for each candidate (modifies T051)
- [ ] T060a [US3] Implement interactive slot selection in `src/cli/main.py`: when PolicyDecision contains action="propose_candidates", present 3 options to user with Rich table, accept user input (1-3 or 'cancel'), update state with selected slot and re-invoke graph with confirmed time (addresses FR-014)
- [ ] T061 [US3] Implement `src/graph/edges.py`: create conditional_edge_from_conflict(state: SchedulerState) -> str that routes to "confirm_or_adjust" if conflicts detected or weather high risk, else routes to "create_event" (same file as T040)
- [ ] T062 [US3] Update `src/graph/builder.py`: ensure graph flow includes conflict check between weather and decision: intent_and_slots → check_weather → find_free_slot → confirm_or_adjust → create_event
- [ ] T063 [US3] Update `src/services/formatter.py`: add Rich table formatting for conflict alternatives showing 3 rows with columns: option number (1-3), time, duration available, format as interactive selection prompt

**RUN TESTS - SHOULD PASS**

### Refactoring for User Story 3

- [ ] T064 [US3] Refactor find_free_slot_node: extract candidate generation logic to calendar_utils.py, add unit tests for find_next_available_slots(current_time, conflicts, duration) → list of candidates
- [ ] T065 [US3] Add integration test for conflict selection: test full flow where user selects option 2 from alternatives → event created at new time with summary

**Checkpoint**: User Story 3 complete - conflict resolution works with 3 alternatives, clear formatting, tests pass

---

## Phase 6: User Story 4 - Process Visualization (Priority: P4)

**Goal**: Generate visual flowchart of decision-making process for developers to understand system logic

**Independent Test**: Run visualization export command → verify Mermaid/Graphviz file generated with all nodes and edges labeled

### Tests for User Story 4 (Test-First)

- [ ] T066 [P] [US4] Create `tests/unit/test_visualizer.py`: test export_to_mermaid(graph) returns string with mermaid syntax, test export_to_graphviz(graph) returns DOT format string, test all 6 nodes present in output, test edge labels include conditions
- [ ] T067 [US4] Create `tests/integration/test_visualization_export.py`: test `weather-scheduler visualize` CLI command creates graph/flow.svg and graph/flow.mermaid files, verify files exist and non-empty, verify mermaid embeddable in markdown

**RUN TESTS - SHOULD FAIL**

### Implementation for User Story 4

- [ ] T068 [P] [US4] Create `src/graph/visualizer.py`: implement export_to_mermaid(graph: StateGraph) -> str that calls graph.get_graph().draw_mermaid(), adds node labels and edge condition annotations, returns mermaid string
- [ ] T069 [P] [US4] Create `src/graph/visualizer.py`: implement export_to_graphviz(graph: StateGraph) -> str that converts graph to DOT format with graphviz library, adds node shapes (rectangles for process, diamonds for decisions), adds edge labels (same file as T068)
- [ ] T070 [US4] Create `src/graph/visualizer.py`: implement save_visualization(graph: StateGraph, output_dir: str) that exports both mermaid and svg formats, creates output_dir if not exists, writes to flow.mermaid and flow.svg files (same file as T068)
- [ ] T071 [US4] Update `src/cli/main.py`: add visualize() command that loads graph config, builds graph, calls save_visualization(), displays success message with file paths
- [ ] T072 [US4] Update `src/graph/builder.py`: add node metadata for visualization: labels (human-readable names), descriptions (what each node does), condition descriptions for edges

**RUN TESTS - SHOULD PASS**

### Documentation for User Story 4

- [ ] T073 [US4] Create `specs/001-weather-aware-scheduler/quickstart.md`: write installation instructions (`pip install -e .`), basic usage examples for 3 scenarios (sunny/rainy/conflict), troubleshooting section for common errors, configuration section for graph.config.yaml
- [ ] T074 [US4] Update README.md: embed graph/flow.svg with explanation of decision nodes (intent_and_slots, check_weather, find_free_slot, confirm_or_adjust, create_event, error_recovery), add legend for node types and edge conditions
- [ ] T075 [US4] Create `docs/architecture.md`: document system overview, 6 node responsibilities with input/output, data flow diagram, tool architecture (mock vs MCP), state management strategy

**Checkpoint**: User Story 4 complete - visualization exports work, documentation explains system logic, new users can understand flow in <5 minutes

---

## Phase 7: Cross-Story Integration & Error Handling

**Goal**: Implement error recovery node and ensure all user stories work together seamlessly

**Purpose**: Polish and error handling that affects multiple user stories

### Tests for Error Handling (Test-First)

- [ ] T076 [P] Create `tests/integration/test_missing_slot.py`: test input "Meet Alice tomorrow" (missing time/location) → clarification question asked, after response → event created successfully, verify one-shot strategy (exactly 1 clarification round)
- [ ] T077 [P] Create `tests/integration/test_service_failure.py`: test mock tool raises WeatherServiceError → retry once → graceful degradation with notes="Manual weather check recommended", verify event still created
- [ ] T078 [P] Create `tests/contract/__init__.py` empty file
- [ ] T079 [P] Create `tests/contract/test_weather_contract.py`: test MockWeatherTool returns WeatherCondition with required fields (prob_rain, risk_category, description), test raises WeatherServiceError on failure (not generic exception)
- [ ] T080 [P] Create `tests/contract/test_calendar_contract.py`: test MockCalendarTool find_free_slot() returns dict with status/candidates, test create_event() returns CalendarEvent with event_id

**RUN TESTS - SHOULD FAIL**

### Implementation for Error Handling

- [ ] T081 Implement `src/graph/nodes.py`: create error_recovery_node(state: SchedulerState) -> SchedulerState with logic: if clarification_needed generate precise follow-up question with examples (one-shot attempt), on second failure provide format examples and return error summary "Unable to parse - please provide time (e.g. 2pm, 14:00), location (e.g. Taipei), duration (e.g. 60min)", if tool failures add degradation notes (same file as T038) (addresses analysis finding U1)
- [ ] T082 Implement `src/graph/edges.py`: create conditional_edge_from_error(state: SchedulerState) -> str that routes back to "intent_and_slots" if clarification answered, to "create_event" if degraded, to END if fatal error (same file as T040)
- [ ] T083 Update `src/graph/builder.py`: wire error_recovery_node into graph with edges from all nodes that can fail (intent_and_slots, check_weather, find_free_slot), ensure loop-back for clarification
- [ ] T084 Update `src/tools/mock_weather.py`: add raise_on_error parameter for testing, if True raise WeatherServiceError("Service unavailable")
- [ ] T085 Update `src/tools/mock_calendar.py`: add raise_on_error parameter for testing, if True raise CalendarServiceError("Service unavailable")
- [ ] T086 Update `src/lib/retry.py`: enhance retry decorator to catch specific exceptions (WeatherServiceError, CalendarServiceError), log retry attempts, return None after max attempts (graceful failure)
- [ ] T087 Update `src/cli/prompts.py`: add clarification question templates with examples ("Time: e.g. 2pm, 14:00, afternoon"), add service failure messages with actionable guidance

**RUN TESTS - SHOULD PASS**

### Final Integration Tasks

- [ ] T088 Create `datasets/eval_min5.jsonl`: 5 golden-path test cases in JSONL format: (1) sunny path "Friday 2pm Taipei meet Alice 60min", (2) rainy adjustment "Tomorrow afternoon Taipei coffee rain backup", (3) conflict "Friday 3pm team sync 30min", (4) missing slot "Meet Alice tomorrow", (5) service failure with error flag
- [ ] T089 [P] Create `scripts/replay_eval.py`: load datasets/eval_min5.jsonl, invoke graph for each case, compare output with expected results, calculate success rate, print report (target 100% with mock)
- [ ] T090 [P] Create `scripts/dev_run.sh`: bash script that runs `source .env`, `uv sync`, `weather-scheduler schedule "Friday 2pm Taipei meet Alice 60min"`, `weather-scheduler visualize`, make executable with chmod +x
- [ ] T091 Run full integration test suite: `pytest tests/integration/ -v` → verify all 5 golden paths pass (sunny, rainy, conflict, missing, failure)
- [ ] T092 Run unit test suite with coverage: `pytest tests/unit/ -v --cov=src --cov-report=term` → verify ≥90% coverage for business logic (services, models)
- [ ] T093 Run contract tests: `pytest tests/contract/ -v` → verify tool contracts consistent (mock tools match expected interfaces)
- [ ] T094 Run dataset replay: `python scripts/replay_eval.py` → verify 5/5 success (100% pass rate)
- [ ] T095 Validate test suite performance: `pytest tests/ --durations=0` → verify total time <5s (constitutional requirement)

**Checkpoint**: All 4 user stories integrated, error handling complete, all tests pass, 5 golden paths 100% success

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, documentation, and final validation

- [ ] T096 [P] Add progress indicators to `src/cli/main.py`: use Rich spinners for operations >500ms (weather check, conflict check), show "Processing..." message with animation
- [ ] T097 [P] Implement `--json` flag in `src/cli/main.py`: add flag to schedule command that outputs machine-readable JSON instead of Rich formatted text (EventSummary.model_dump_json())
- [ ] T098 [P] Add `test-replay` command to `src/cli/main.py`: implement CLI command that runs scripts/replay_eval.py and displays results
- [ ] T099 [P] Improve error messages in `src/cli/prompts.py`: add examples of valid formats to all error messages ("Friday 2pm", "2025-10-17 14:00"), ensure actionable guidance ("Please provide...")
- [ ] T100 [P] Update `specs/001-weather-aware-scheduler/quickstart.md`: finalize all sections (installation, usage, 4 demo scenarios, troubleshooting, configuration, visualization command)
- [ ] T101 [P] Create `docs/FAQ.md`: answer questions "How to add a new weather condition?", "How to extend to multi-day events?", "How to switch from mock to real APIs?", "How to customize time shift window?"
- [ ] T102 [P] Code cleanup pass 1 - `src/models/`: ensure all Pydantic models have docstrings, type hints complete, validators documented with examples
- [ ] T103 [P] Code cleanup pass 2 - `src/services/`: refactor any functions >50 lines, extract constants to module level, ensure single responsibility per function
- [ ] T104 [P] Code cleanup pass 3 - `src/graph/`: ensure nodes are <50 lines each, extract complex logic to services, add comprehensive error handling and logging
- [ ] T105 Run ruff format and ruff check: `ruff format src/ tests/ && ruff check src/ tests/` → fix any linting issues
- [ ] T106 Run mypy type checking: `mypy src/` → fix any type errors, ensure strict mode passes
- [ ] T107 Run pre-commit hooks: `pre-commit run --all-files` → verify all checks pass (ruff, mypy, pytest)
- [ ] T108 Performance validation: run benchmarks for 5 golden paths, measure end-to-end latency, verify SC-006 (<3s request) and SC-008 (<1s conflict detection) met
- [ ] T109 Create `specs/001-weather-aware-scheduler/performance.md`: document benchmark results with table (test case, latency p50/p95, memory usage), confirm constitutional requirements met
- [ ] T110 Final validation against Definition of Done: verify 3 CLI demos work, flowchart generated, 5 golden tests pass, all outputs include reason+notes, clarification ≤1 round, error messages user-friendly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Stories (Phases 3-6)**: All depend on Foundational phase completion
  - **Phase 3 (US1 - P1)**: Start immediately after Foundational - **MVP baseline**
  - **Phase 4 (US2 - P2)**: Can start after US1 complete (needs working graph and nodes)
  - **Phase 5 (US3 - P3)**: Can start after US1 complete (needs working graph and nodes)
  - **Phase 6 (US4 - P4)**: Can start after Phase 3 complete (needs working graph to visualize)
- **Cross-Story Integration (Phase 7)**: Depends on US1-US3 complete (error handling touches all flows)
- **Polish (Phase 8)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) complete - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 implementation (needs graph infrastructure, nodes.py, CLI from US1)
- **User Story 3 (P3)**: Depends on US1 implementation (needs graph infrastructure, nodes.py, CLI from US1) - Can run in parallel with US2
- **User Story 4 (P4)**: Depends on US1 implementation (needs working graph to visualize) - Can run in parallel with US2/US3

### Within Each User Story

- **Test-First**: Tests MUST be written and MUST FAIL before implementation (TDD red phase)
- **Implementation**: Write minimum code to make tests pass (TDD green phase)
- **Refactoring**: Clean up code while keeping tests passing (TDD refactor phase)
- **Story complete**: All tests passing + independent validation criteria met

### Parallel Opportunities

- **Setup tasks (Phase 1)**: T003-T009 can all run in parallel (different config files)
- **Foundational tasks (Phase 2)**: T010-T013 (models), T015-T017 (tool interfaces), T020-T024 (utilities) can run in parallel
- **US1 tests**: T027-T032 can all run in parallel (different test files)
- **US1 services**: T034-T037 can run in parallel (different service files)
- **US2 tests**: T048-T049 can run in parallel with US1 implementation if US1 tests already written
- **US3 implementation**: T059-T063 can overlap with US2 refactoring (T055-T056) if careful about nodes.py changes
- **US4 implementation**: T068-T070 (visualizer functions) can run in parallel
- **Error handling tests**: T076-T080 can all run in parallel (different test files)
- **Polish tasks**: T096-T104, T109 can run in parallel (different files/concerns)

---

## Parallel Example: User Story 1 Implementation

After all US1 tests are written and failing (T027-T033):

```bash
# Launch all service implementations in parallel (different files):
Task T034: Create src/services/parser.py
Task T035: Create src/services/validator.py
Task T036: Create src/services/time_utils.py
Task T037: Create src/services/formatter.py

# Then sequentially (all touch nodes.py):
Task T038: Implement intent_and_slots_node in src/graph/nodes.py
Task T039: Implement create_event_node in src/graph/nodes.py
Task T040: Implement conditional edges in src/graph/edges.py
Task T041: Wire nodes into graph in src/graph/builder.py

# Then CLI (depends on graph working):
Task T043: Create src/cli/main.py
Task T044: Create src/cli/prompts.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T009)
2. Complete Phase 2: Foundational (T010-T026) **CRITICAL - blocks all stories**
3. Complete Phase 3: User Story 1 (T027-T047)
4. **STOP and VALIDATE**: Run `pytest tests/integration/test_sunny_path.py` → should pass
5. **STOP and VALIDATE**: Run `weather-scheduler schedule "Friday 2pm Taipei meet Alice 60min"` → should create event
6. **Checkpoint**: MVP complete - can schedule simple meetings

### Incremental Delivery (MVP → P2 → P3 → P4)

1. **MVP (US1)**: Complete Phase 1-3 → Test independently → Deploy/Demo
   - Users can schedule meetings with natural language
   - Simple, clear output with structured summaries
   - **Value delivered**: Faster than manual calendar tools

2. **Add Weather-Aware (US2)**: Complete Phase 4 → Test independently → Deploy/Demo
   - Users get weather-based suggestions
   - Adjustments include clear reasoning
   - **Value delivered**: Prevent weather disruptions

3. **Add Conflict Resolution (US3)**: Complete Phase 5 → Test independently → Deploy/Demo
   - Users get conflict detection and alternatives
   - 3 options presented with durations
   - **Value delivered**: Prevent double-booking

4. **Add Visualization (US4)**: Complete Phase 6 → Test independently → Deploy/Demo
   - Developers understand system logic
   - Flowchart embeddable in docs
   - **Value delivered**: Easier debugging and extension

5. **Integrate & Polish**: Complete Phase 7-8 → Full validation → Deploy
   - Error handling works across all stories
   - All 5 golden paths pass
   - Documentation complete

### Parallel Team Strategy

With multiple developers:

1. **Team completes Setup + Foundational together** (Phase 1-2)
2. **Once Foundational done**:
   - **Developer A**: User Story 1 (P1) - Focus on MVP
   - **Developer B**: Wait for US1 graph infrastructure (T038-T041), then start User Story 2 (P2) tests
   - **Developer C**: Wait for US1 graph infrastructure, then start User Story 3 (P3) tests
3. **After US1 nodes/graph/CLI ready**:
   - **Developer B**: Complete US2 implementation (weather logic)
   - **Developer C**: Complete US3 implementation (conflict logic)
   - **Developer D**: Start User Story 4 (P4) visualization (depends only on graph existing)
4. **After US1-US3 done**:
   - **Any developer**: Phase 7 integration (error handling)
5. **Final phase**:
   - **All developers**: Phase 8 polish tasks in parallel (T096-T104 different files)

---

## Notes

- **[P] tasks** = different files, no dependencies, safe to parallelize
- **[Story] label** (US1/US2/US3/US4) maps task to specific user story for traceability
- **Each user story is independently completable and testable** - can stop after any story and have working system
- **Test-first mandatory per constitution**: Write tests, see them fail, then implement (Red-Green-Refactor)
- **Commit after each task or logical group** (e.g., all US1 tests, all US1 services)
- **Stop at any checkpoint to validate story independently** - don't proceed if tests failing
- **Total task count**: 112 tasks across 8 phases (added T051a for policy helpers, T060a for slot selection)
- **Estimated MVP completion**: ~40 tasks (T001-T047, through Phase 3 = User Story 1)
- **Analysis-driven improvements**: Tasks updated based on /speckit.analyze findings (C1, U1, U2, I1, FR-014)
- **Constitution compliance**: 100% coverage for critical paths (T029-T033, T048-T049, T057-T058, T076-T077), <5s test suite (validated in T095), test-first approach enforced

---

## Success Criteria Validation

After completing all phases, verify:

- [ ] **SC-002**: System achieves 100% success rate on 5 golden-path test scenarios (validated by T094)
- [ ] **SC-006**: System processes requests in <3s (validated by T108)
- [ ] **SC-008**: Conflict detection <1s (validated by T108)
- [ ] **Constitution**: Test suite <5s total (validated by T095)
- [ ] **Constitution**: Coverage ≥100% critical paths, ≥90% business logic (validated by T092)
- [ ] **Definition of Done**: 3 CLI demos work (T110), flowchart generated (T071), 5 golden tests pass (T091), outputs include reason+notes (T110), clarification ≤1 (T076), errors user-friendly (T099)
