# Phase 7 Plan: Local weekly automation

**Status:** Done 2026-11-14. Closed on manual `--force` runs (acceptance 3 dropped by user). Planned 2026-11-14. Overrides the Phase 7 row in the master plan (GitHub Actions replaced by a local Task Scheduler job).

## Goal

One command pulls fresh data, rebuilds tables, picks all three teams, plans chips and writes a round report. Windows Task Scheduler runs it daily so the report is ready before each lock without a manual run.

## Decisions (grilling 2026-11-13/14)

- Runs locally, not on GitHub Actions. Why: the repo is public, so committed reports, logs and artifacts would expose the picks; team files are updated by hand anyway.
- Team files (`config/my_team_1..3.yaml`) stay manual. The report warns when a team file was last edited before the previous round's race.
- Task Scheduler runs `uv run python -m pipelines.weekly_update` daily at 20:00 local, catch-up on missed runs, only when the user is logged on (no stored password).
- The script exits unless the next lock is under 48 hours away and no successful report exists for that round. `--force` always runs and rewrites the report.
- Output: `reports/round_{season}_{round:02d}.md` (gitignored) and `reports/weekly_update.log`.
- The run never reads `F1_DATA_KEY`. It pulls into plaintext `data/raw/` (gitignored); sealing and committing stay manual. The report counts unsealed raw files.
- Report: header (season, round, track, lock in local time, generated time); per team the `pick_team.py` and `plan_chips.py` output plus the stale-file warning; data check (latest price round, unsealed files).
- A failing step stops the run, writes a report headed `FAILED at <step>` with the last error line, and logs the full trace. The next daily run retries. No desktop popup.

## Tasks

| # | Task | Who | Files | Depends on | Status |
|---|---|---|---|---|---|
| 7.1 | `weekly_update.py`: gate, `--force`, pulls (official snapshot, Jolpica, TracingInsights latest tag, mzafram), rebuild, picks and chips for every team file, report, failure report, log; gitignore reports | Claude, worktree `../f1-fantasy-7.1-weekly`, branch `claude/7.1-weekly` | `pipelines/weekly_update.py`, `tests/test_weekly_update.py`, `.gitignore` | - | Done 2026-11-14 (7a4cab6): `--force` wrote `reports/round_2026_21.md` for all three teams |
| 7.2 | `scripts/install_task.ps1`, `scripts/uninstall_task.ps1`, "how to run" in `docs/how-it-works.md` | ChatGPT, worktree `../f1-fantasy-7.2-scheduler`, branch `chatgpt/7.2-scheduler` | `scripts/*.ps1`, `docs/how-it-works.md` | - | Done 2026-11-14 (merged; battery defaults in known-issues) |

## Acceptance

1. Tests: gate skips beyond 48 h or with a successful report, runs on a FAILED report or `--force`; a failing step writes the FAILED report; stale team-file warning; the module never mentions `F1_DATA_KEY` or the vault.
2. A manual `--force` run writes a full report for the next 2026 round with all three teams.
3. ~~Task Scheduler runs it unattended once before a real 2026 lock.~~ Dropped 2026-11-14: user runs `--force` by hand before each lock; the task scripts stay available but are not installed.
4. Decisions in `docs/decisions.md`.
