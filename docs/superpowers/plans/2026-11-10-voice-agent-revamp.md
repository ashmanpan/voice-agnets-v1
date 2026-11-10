# Voice Agent Revamp — Master Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (Native, chosen) to implement task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden and modernize the existing LiveKit outbound voice-agent (fix all audit findings), then make the voice pipeline provider-pluggable so it can run the current stack, ElevenLabs TTS (Option 2), and a speech-to-speech mode (Option 3) behind one config flag.

**Architecture:** Keep the working FastAPI + LiveKit-Agents design; do not rewrite. Add an offline test harness first, then layer safety (auth/CORS/rate-limit), modularization, migrations, a durable task runner, dependency bumps, and observability. Finally introduce a provider-abstraction layer in the agent so STT/LLM/TTS and whole-pipeline mode are selected by config, enabling Options 2 and 3 as additive, fallback-safe changes.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.x + Alembic, LiveKit Agents 1.x, Groq (LLM), OpenAI (STT/TTS), ElevenLabs (new TTS), OpenAI Realtime (new S2S), pytest, React 19 / Vite 7 (frontend, largely current), Docker Compose. Validation is **offline automated tests with mocked providers** — no live phone calls in this environment.

**Spec:** this document (brainstorming outcome folded in; see Intent & Scope below).

---

## Intent & Scope

**Why now:** The app was built ~6–12 months ago across 8 fast "DROP" iterations. It works but has zero automated tests, no auth, a 1,769-line `main.py` monolith, ad-hoc migrations, aged backend deps, and no observability. The owner wants a clean, safe foundation and then two voice upgrades (ElevenLabs, S2S).

**Goals:**
- Fix all 17 audit findings.
- Make the voice pipeline provider-pluggable; add ElevenLabs TTS (Opt 2) and an S2S mode (Opt 3) without breaking the existing stack.
- Give the agent **tool-use**: connect MCP servers and skill/tool modules so the LLM can perform real tasks mid-call (function-calling), with connections managed as background services.
- Every behavior change is pinned by an offline test.

**Non-goals (this revamp):**
- Rewriting the frontend (React 19/Vite 7 stack is current; only wiring/test gaps are touched).
- Self-hosted S2S on vLLM (Opt 3b) — tracked as a later spike, not built here.
- Live load/latency benchmarking (needs real calls on the owner's machine).

**Anti-goals (would make this a failure even if it "works"):**
- Any change that lets an unauthenticated caller trigger a real phone call.
- A refactor that silently changes call/task behavior with no test proving parity.
- New hard dependency on a single paid voice vendor with no fallback.

**Constraints:**
- Work on branch `revamp/audit-fixes-and-voice-options`, commit incrementally, local only (no push until review).
- Secrets stay in git-ignored `.env`; never commit real keys.
- Validation = offline tests; provider SDKs are mocked in tests.

## Global Constraints

- Python target: **3.11+** (match container runtime; code must import under 3.11).
- Backend deps re-pinned to current stable majors in Phase 6; until then, don't assume un-pinned versions.
- All new/changed FastAPI routes that trigger calls, cost money, or mutate data require the auth dependency from Phase 2.
- Provider/vendor SDK calls (`openai`, `groq`, `elevenlabs`, LiveKit plugins) are **never** invoked for real in tests — inject fakes.
- Existing call/task DB semantics documented in `CURRENT_STATE.md` are the behavioral baseline; parity tests assert them.

## Review Focus

Inputs/conditions the spec implies but that are easy to break; each gets a test in the owning task:
1. **Unauthenticated call-trigger** — `POST /api/calls/*` and `/api/tasks/{id}/call` without/with a bad key must return 401, never dispatch an agent (Phase 2).
2. **CORS preflight from the frontend origin** — `OPTIONS` from the Vite origin must succeed; a non-allowlisted origin must not get credentials (Phase 2).
3. **Rate-limit breach** — N+1 call-trigger requests in the window return 429, not an (N+1)th phone call (Phase 2).
4. **Provider failure / fallback** — when the selected TTS/STT provider raises, the pipeline falls back to the default provider rather than dropping the call (Phase 9).
5. **Unknown `PIPELINE_MODE` / provider name** — an invalid config value fails fast at startup with a clear error, not mid-call (Phase 9/10).

---

## Phase Roadmap (scope to approve)

Each phase ends with working, tested software and its own commit(s). Phases 2–10 get their detailed task breakdown written **just before** that phase starts (so later phases benefit from the test harness and from what earlier phases reveal). Phase 1 is fully detailed below.

| Phase | Theme | Audit items | Dependency |
|------|-------|-------------|------------|
| **1** | Test harness + CI foundation | #5 | none — do first |
| **2** | Safety: auth, CORS, rate-limiting | #1,#2,#3,#4 | Phase 1 |
| **3** | Backend modularization (routers/services/schemas) | #6 | Phase 1–2 |
| **4** | Alembic migrations | #7 | Phase 3 |
| **5** | Durable task runner (replace raw threads) | #8 | Phase 3 |
| **6** | Dependency modernization + pinning | #9 | Phase 1 (tests green across bump) |
| **7** | Telephony path consolidation (Twilio vs LiveKit) | #10 | Phase 3 |
| **8** | Observability (Langfuse + structured logging) | #14 | Phase 3 |
| **9** | Provider abstraction + **ElevenLabs TTS (Option 2)** | #11,#12,#13 | Phase 1 |
| **10** | **S2S mode (Option 3a: OpenAI Realtime)** | Opt 3 | Phase 9 |
| **11** | **Agent tool-use: MCP servers + skills (function-calling mid-call)** | new | Phase 3 (services) + Phase 9 (LLM abstraction) |
| **Cleanup** | Delete stale `../voice-agents`, consolidate docs, pin LiveKit agents ≥1.0 | #15,#16,#17 | folded into phases |

> Note: Phase 9 (ElevenLabs) depends only on Phase 1, so if the owner wants the voice win sooner, Phases 2→9 can be reordered after Phase 1. Default order above does safety first.

---

## Phase 1 — Test Harness + CI Foundation (DETAILED)

**Rationale:** Nothing else can be refactored safely without tests. This phase adds pytest, a FastAPI test client with a disposable DB, provider fakes, a first real parity test, and a CI workflow — the net it all falls into.

### Task 1.1: pytest + test DB fixtures

**Files:**
- Create: `app/tests/__init__.py`, `app/tests/conftest.py`
- Create: `pytest.ini`
- Create: `requirements-dev.txt`
- Test: `app/tests/test_smoke.py`

**Interfaces:**
- Produces: pytest fixture `client` (a `fastapi.testclient.TestClient` bound to `app.main:app` with the DB dependency overridden to a transactional SQLite or ephemeral Postgres session); fixture `db_session`.
- Consumes: `app.main:app`, `models.get_db` (overridden via `app.dependency_overrides`).

- [ ] **Step 1: Write the failing smoke test**
```python
# app/tests/test_smoke.py
def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
```
- [ ] **Step 2: Run it, verify it fails** — `pytest app/tests/test_smoke.py -v` → FAIL (no `client` fixture / import error).
- [ ] **Step 3: Implement `conftest.py`** — define `client` and `db_session` fixtures: create an in-memory/temp SQLite engine (or testcontainers Postgres if SQLite incompat is hit), create tables from `models.Base.metadata`, override `models.get_db` via `app.dependency_overrides`. Add `requirements-dev.txt` (`pytest`, `httpx`). Add `pytest.ini` with `pythonpath = app`.
- [ ] **Step 4: Run it, verify it passes** — `pytest app/tests/test_smoke.py -v` → PASS.
- [ ] **Step 5: Commit** — `git add app/tests pytest.ini requirements-dev.txt && git commit -m "test: add pytest harness with FastAPI client + test DB"`

> Decision point the executor cannot make alone: if `models.py` or endpoints hard-require Postgres-specific types (e.g. JSONB) and SQLite can't host the schema, switch the fixture to an ephemeral Postgres (docker/testcontainers). Prefer SQLite; fall back to Postgres only if table creation fails.

### Task 1.2: Provider fakes (no real API calls in tests)

**Files:**
- Create: `app/tests/fakes.py`
- Test: `app/tests/test_fakes.py`

**Interfaces:**
- Produces: `FakeLiveKitDispatcher` (records dispatch calls, never hits network) and a pytest `autouse` fixture `block_external` that monkeypatches outbound LiveKit/OpenAI/Groq entrypoints used by `main.py` to raise if called unexpectedly.
- Consumes: the dispatch function in `app/main.py` that triggers the LiveKit agent (identify its exact symbol during implementation).

- [ ] **Step 1: Write failing test** — `test_call_trigger_uses_fake_dispatch`: posting to the call-trigger endpoint records one dispatch on `FakeLiveKitDispatcher` and makes zero real network calls.
- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Implement `fakes.py`** + wire the `autouse` fixture into `conftest.py`; inject the fake via `dependency_overrides` or monkeypatch of the dispatch symbol.
- [ ] **Step 4: Run, verify pass.**
- [ ] **Step 5: Commit** — `git commit -m "test: add provider fakes + block real external calls in tests"`

### Task 1.3: First behavioral parity test (calls list/detail)

**Files:**
- Test: `app/tests/test_calls_api.py`

**Interfaces:**
- Consumes: `client`, `db_session`, existing call endpoints (`GET /api/calls/{id}`, and whichever endpoint lists calls — confirm during implementation; audit found **no plain `GET /api/calls`**, so this task also records that gap as an xfail or a documented finding).

- [ ] **Step 1: Write tests** — seed a `Call` + `TranscriptSegment` via `db_session`; assert `GET /api/calls/{id}` returns it with transcript; assert the documented list behavior. Mark the missing `GET /api/calls` list endpoint with `pytest.mark.xfail(reason="audit #gap: no calls-list endpoint")`.
- [ ] **Step 2: Run, verify** the detail tests pass and the xfail is xfailed (not xpassed).
- [ ] **Step 3:** (no product code — this task pins current behavior.)
- [ ] **Step 4: Commit** — `git commit -m "test: pin calls API behavior; mark missing calls-list endpoint"`

### Task 1.4: CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Produces: a GitHub Actions job that installs `requirements.txt` + `requirements-dev.txt` and runs `pytest`. (It will run once pushed; locally we verify the commands it runs.)

- [ ] **Step 1:** Write `ci.yml` (checkout, setup-python 3.11, pip install, `pytest`). Frontend lint/build job optional stub.
- [ ] **Step 2: Verify locally** — run the exact install + `pytest` commands the workflow uses; expected: PASS.
- [ ] **Step 3: Commit** — `git commit -m "ci: run pytest on push/PR"`

**Phase 1 exit criteria:** `pytest` green locally; harness can seed DB, call endpoints, and block real provider calls; CI file present.

---

## Phases 2–10 (OUTLINE — detailed before each starts)

### Phase 2 — Safety
- API-key/bearer auth dependency; apply to all `/api/*` mutating + call-trigger routes. Tests: 401 on missing/bad key (Review Focus #1).
- CORS middleware scoped to frontend origin(s) from env; + Vite dev proxy. Tests: preflight allow/deny (Review Focus #2).
- Rate limiting (`slowapi`) on call-trigger routes. Tests: 429 past threshold (Review Focus #3).

### Phase 3 — Modularization
- Split `main.py` into `app/routers/{calls,tasks,actions,contacts,reports,webhooks}.py`, `app/services/`, `app/schemas/`. Behavior-parity tests from Phase 1 must stay green throughout. Add the missing `GET /api/calls` list endpoint (flips the Task 1.3 xfail to pass).

### Phase 4 — Alembic
- Introduce Alembic; baseline migration = current `schema.sql`; port `add_*_table.py`/`migrate_db.py` into versioned migrations; retire ad-hoc scripts.

### Phase 5 — Durable task runner
- Replace raw `threading.Thread` background work with `arq` (or FastAPI `BackgroundTasks` as interim); retries + visibility. Tests with a fake queue.

### Phase 6 — Dependency modernization
- Bump + re-pin backend deps (FastAPI, SQLAlchemy, pydantic, groq, openai, livekit*); run full test suite as the gate at each bump. Align `livekit-agent/requirements.txt` to `livekit-agents>=1.0` (Cleanup #17).

### Phase 7 — Telephony consolidation
- Decide LiveKit SIP as the path; quarantine/remove unused `/twilio/*` TwiML flow (confirm with owner which is live) behind tests.

### Phase 8 — Observability
- Structured logging + Langfuse instrumentation of LLM/agent turns (owner already runs Langfuse locally). Per-stage latency logged.

### Phase 9 — Provider abstraction + **ElevenLabs (Option 2)**
- Define `TTSProvider`/`STTProvider` interfaces + a factory keyed by `TTS_PROVIDER`/`STT_PROVIDER` env (default = current OpenAI). Add `elevenlabs` TTS impl + `livekit-plugins-elevenlabs`. Fallback to default on provider error (Review Focus #4). Invalid provider name fails fast at startup (Review Focus #5). Tests with fakes; no real TTS calls.

### Phase 10 — **S2S (Option 3a: OpenAI Realtime)**
- Add `PIPELINE_MODE` (`cascade` default | `realtime`); a realtime entrypoint using the LiveKit OpenAI Realtime integration; transcript capture preserved. Opt-in per call; cascade remains default/fallback. Tests assert mode selection + config validation.

### Phase 11 — Agent tool-use: MCP servers + skills
- Register **function tools** with the LiveKit `AgentSession` so the LLM can call them mid-conversation (works in both cascade and realtime modes; Groq Llama-3.3 and OpenAI Realtime both support tool-calling).
- Connect one or more **MCP servers** as tool sources (LiveKit Agents 1.x `mcp` integration), started/supervised as background services alongside the agent worker; tools are discovered from the server and exposed to the LLM.
- Add a thin **skill/tool registry** so local tool modules ("skills") can be registered the same way as MCP tools.
- Safety: tool calls that mutate data or cost money go through the Phase 2 auth/service layer; every tool call is logged/traced (Phase 8). Tests use a fake MCP server + fake tools; no real external tool execution.
- **Open questions to resolve before detailing this phase** (owner input needed):
  1. Which MCP servers / what tasks should the agent be able to do on a call (e.g. CRM lookup, calendar, ticketing, DB updates)?
  2. Does "skill" mean Anthropic/Claude-style skills, your own tool packages, or the MCP tools themselves?
  3. Should tool connections be global to the worker, or per-call/per-tenant (different customers → different tools)?
  4. Human-in-the-loop: can the agent execute money/data-mutating actions autonomously, or must it confirm with the caller / queue for approval?

### Cleanup (folded in)
- Delete stale empty `../voice-agents/` (#15). Consolidate ~15 status markdowns + `old-md-files/` into `README.md` + `ARCHITECTURE.md`; fix the Deepgram-vs-Whisper doc contradiction (#16). Commit the in-flight agent change — done in branch baseline (#17).

---

## Self-Review notes
- **Spec coverage:** all 17 audit items mapped to a phase in the roadmap table; Opt 2 → Phase 9, Opt 3 → Phase 10. ✅
- **Review Focus:** 5 items listed; each assigned to an owning phase/task with a test. ✅
- **Proportion:** Phase 1 detailed (highest risk, enables all else); Phases 2–10 outlined to avoid transcribing code before the harness and refactor reveal exact signatures — each is detailed just-in-time per the roadmap. ✅
