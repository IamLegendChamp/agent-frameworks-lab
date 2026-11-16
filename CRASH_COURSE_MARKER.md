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
- `a2a_lab/` (whole folder, F4 A2A lane; added 2026-11-16): `__init__.py`, `policy_agent.py`, `policy_server.py`, `policy_caller.py`, `card_keys.py` (card signing key pair; keys go to the git-ignored `.keys/`), `security.py` (bearer-token middleware, allow-list, audit), `test_a2a_security.py` (pytest, 12 checks)
- `mao_lab/` (whole folder, F5 multi-agent orchestration; added 2026-11-16): `__init__.py`, `graph.py` (supervisor, workers, hop limit, approval gate), `tools.py` (refund ledger with idempotency), `runner.py`, `run_demo.py`, `test_mao_graph.py` (pytest, 9 checks)

## Edits under the marker (undo when it ends)

- `logging_setup.py` (hand-written file): added `"a2a_lab"`, `"mcp_lab"` and `"mao_lab"` to `PROJECT_LOGGERS` so imported modules log at INFO (2026-11-16); on ending the marker the learner decides whether to keep it (it is needed for any module not run as `__main__`)
- `pyproject.toml` and `uv.lock`: `uv add a2a-sdk` (2026-11-16) and `uv add "a2a-sdk[http-server,signing]"`; on ending the marker run `uv remove a2a-sdk` (the lane 2 dependency goes with the marker code)

## Outside the marker (stay)

- `mcp_lab/policy_server.py`, `mcp_lab/policy_client.py`, `mcp_lab/agent_mcp.py`, `mcp_lab/idp.py`, `mcp_lab/auth_tests.py` (the learner wrote these by hand)
- `.gitignore` entry `.keys/` (security fix, added 2026-11-16)
- `pyproject.toml` and `uv.lock` changes from `uv add`
- F3 notes and tick (README lane list, `TOOL_DECISIONS.md` result block, `HANDOFF.md`), written 2026-11-16 after the marker started; they are documentation and stay
