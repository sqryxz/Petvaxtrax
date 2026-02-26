# PETVAX DOER RUN

You are executing an automated task run for PetVaxHK. Follow these steps exactly.

## Context
- Working directory: /Users/atlas/.openclaw/workspace
- State file: petvax/agent_state.json
- Lock file: petvax/agent_lock.json
- History dir: petvax/state_history/

## Step 1: Acquire Lock
Read petvax/agent_lock.json. If run_id is NOT null:
- If running_since within last 900 seconds → EXIT with "LOCK_HELD"
- If older than 900 seconds → proceed (stale lock, break it)

Write lock with:
```json
{
  "run_id": "doer-YYYY-MM-DDTHH:MM:SS+08:00",
  "type": "doer",
  "running_since": "YYYY-MM-DDTHH:MM:SS+08:00",
  "ttl_seconds": 900,
  "host": "petvax"
}
```

## Step 2: Load State
Read petvax/agent_state.json into memory.

## Step 3: Snapshot State
Write to petvax/state_history/STATE_YYYY-MM-DD-HH-MM-SS.json
Set rollback_to to this path in the state.

## Step 4: Select Task
Pick ONE task:
1. Prefer next_actions[0]
2. Status must be "ready" or "in_progress"
3. All deps must be done
4. Must fit: ≤max_files_changed_per_run, ≤time_budget_minutes

**If no valid task:**
- If next_actions.length === 0 → GOAL_COMPLETE
- Set task_id = "GOAL_COMPLETE"
- Trigger Planner (spawn sub-agent with planner.md content)
- Write state, release lock, exit
- Else: write state, release lock, exit

## Step 5: Check Decisions Policy
MUST ASK if: deploy/publish, spending, deleting files, new frameworks
If must ask:
- Create decision entry, set task to blocked
- Update next_actions to next ready task
- Go to Step 8

## Step 6: Execute Task

**If can complete:**
- Execute the work
- Set status = "done"
- Add evidence: {"kind": "file", "path": "x", "note": "y"}

**If partial:**
- Set status = "in_progress"
- Update progress_pct
- Add checkpoint
- Set resume_hint

## Step 7: Update State
- Remove completed from next_actions
- Add newly-ready follow-ups to next_actions
- Update last_run

## Step 8: Write State + Release Lock
Write petvax/agent_state.json
Write lock with run_id: null to release

## CRITICAL: Error Handling
If ANY error occurs:
1. Write error to last_run.errors[]
2. Release lock (run_id: null)
3. Exit with error message

## Output Format
Report: Task ID, Title, Status, Evidence, Next Action
