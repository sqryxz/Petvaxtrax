# PETVAX PLANNER RUN

You are executing a planning run for PetVaxHK. Your job is to ensure the backlog is healthy.

## Context
- Working directory: /Users/atlas/.openclaw/workspace
- State file: petvax/agent_state.json
- Lock file: petvax/agent_lock.json

## Step 1: Acquire Lock
Read petvax/agent_lock.json. If run_id is NOT null:
- If running_since within 900 seconds → EXIT
- If older than 900 seconds → break lock

Write lock with type: "planner"

## Step 2: Check Triggers
Run if ANY:
- next_actions.length === 0
- >3 tasks blocked
- >2 tasks in_progress >3 days stale
- <5 ready tasks
- definition_of_done has unmet items

If NO trigger → 
- Output simple table with next 3 tasks (id, title, status)
- Release lock, exit

## Step 3: Constraint Audit
Compare last_run against constraints in agent_state.json.
If violations found → generate remediation tasks.

## Step 4: Generate Tasks
For each trigger, create tasks with:
- id, title, status, deps, estimate_minutes

## Step 5: Write State
- Add tasks to backlog[]
- Update next_actions
- Update last_run
- Release lock

## Output
When trigger fires: Full report with triggered items and new tasks
When NO trigger: Simple table:
| ID | Title | Status |
|----|-------|--------|
| 1.1 | Create required directories | done |
| 1.2 | Write JSON schemas | ready |
| 1.3 | Create verifier utilities | ready |

Report: Trigger fired, New tasks (id/title/status), Next actions
