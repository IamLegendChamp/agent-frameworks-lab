# Crash-course marker (agent writes, learner runs)

Started: 2026-11-16, during F3 (MCP), step 5d (auth tests as pytest).

## What this marker means

- Before the marker: files the learner wrote by hand. They stay.
- After the marker: files and code the agent writes so the learner can run them and study the concepts. These are **temporary**. They are committed and pushed for device transfer only.
- When the learner says "end the marker": delete every file listed below, undo every edit listed below, then bring the repo back to the marker point (git tag `marker-start`) and continue from there, with the learner writing the code by hand.
- Until the learner says "end the marker": the agent writes the files and code, the learner runs and reads them.

## Git points

- Tag `marker-start`: the last commit before any marker file. To return: remove the files below, then `git reset --hard marker-start` (confirm with the learner first; it discards later commits).

## Files under the marker (delete when it ends)

- `mcp_lab/test_mcp_auth.py` (pytest suite for the JWT server and allow-list; added 2026-11-16)
- `CRASH_COURSE_MARKER.md` (this file)

## Edits under the marker (undo when it ends)

- none yet

## Outside the marker (stay)

- `mcp_lab/policy_server.py`, `mcp_lab/policy_client.py`, `mcp_lab/agent_mcp.py`, `mcp_lab/idp.py`, `mcp_lab/auth_tests.py` (the learner wrote these by hand)
- `.gitignore` entry `.keys/` (security fix, added 2026-11-16)
- `pyproject.toml` and `uv.lock` changes from `uv add`
- F3 notes and tick (README lane list, `TOOL_DECISIONS.md` result block, `HANDOFF.md`), written 2026-11-16 after the marker started; they are documentation and stay
