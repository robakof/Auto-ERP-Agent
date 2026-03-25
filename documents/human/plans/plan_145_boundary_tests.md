# Plan: #145 Boundary Tests + claimed_by repository fix

## Znaleziony bug (przy okazji)

MessageRepository.get/save/_find_by nie zawierają `claimed_by` w SQL.
Entity ma pole, _row_to_entity czyta z graceful degradation, ale SELECT nie pobiera kolumny.
Fix: dodać claimed_by do SELECT (get, _find_by) + INSERT/UPDATE (save).

## Test Suites — priorytet

| # | Suite | Pliki | Severity | Testów |
|---|-------|-------|----------|--------|
| 1 | Runner↔Repository (claimed_by) | test_boundary_claimed.py | Critical | 4 |
| 2 | Telemetry dedup | test_boundary_telemetry.py | Critical | 3 |
| 3 | Safety gate precision | test_boundary_safety.py | Important | 4 |
| 4 | Legacy API mapping | test_boundary_legacy.py | Important | 4 |
| 5 | Transactions | (existing — 5 tests in test_agent_bus) | Moderate | skip |

Suite 5 skip — już ma 5 dobrych testów w test_agent_bus.py.

## Implementacja

### Krok 1: Fix claimed_by w MessageRepository
- get(): dodać claimed_by do SELECT
- _find_by(): dodać claimed_by do SELECT
- save(): dodać claimed_by do INSERT i UPDATE

### Krok 2: Test Suite 1 — Runner↔Repository
- test_repository_reads_claimed_by: save z claimed_by → get → verify
- test_repository_saves_claimed_by_on_insert: new message z claimed_by → persisted
- test_repository_saves_claimed_by_on_update: update claimed_by → persisted
- test_repository_graceful_degradation_claimed_status: row z status='claimed' → UNREAD

### Krok 3: Test Suite 2 — Telemetry dedup
- test_duplicate_tool_call_ignored: same (session, tool, timestamp) → count=1
- test_different_timestamp_allowed: same session+tool, different timestamp → count=2
- test_live_then_replay_dedup: simulate post_tool_use + jsonl_parser → no duplicate

### Krok 4: Test Suite 3 — Safety gate
- test_safe_commands_allowed: python, git, pytest, mkdir
- test_dangerous_patterns_blocked: rm -rf /, DROP TABLE
- test_command_chain_mixed: safe && unsafe → blocked
- test_destructive_wildcard_blocked: rm *.py → blocked

### Krok 5: Test Suite 4 — Legacy API
- test_flag_human_maps_to_escalation: "flag_human" → MessageType.ESCALATION
- test_info_maps_to_direct: "info" → MessageType.DIRECT
- test_suggestion_status_mapping: "in_backlog" → IMPLEMENTED
- test_mapper_round_trip: Message → dict → verify all fields

## Plik testowy

Jeden plik: `tests/test_boundary.py` z klasami per suite.
