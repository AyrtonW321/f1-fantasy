# Prompt for ChatGPT: Phase 7 task 7.2 (Task Scheduler setup)

You are working in the Python repo `f1-fantasy` (F1 Fantasy optimizer, Windows 11, PowerShell 5.1, `uv`). Read `CLAUDE.md`, `docs/progress.md`, `docs/decisions.md` and the Phase 7 plan `docs/superpowers/plans/2026-11-14-phase-7-automation.md` first. Follow CLAUDE.md hard rules: ask before adding any dependency, no commits to main, no pushes, never read, print or store `F1_DATA_KEY`. Smallest correct diff.

## Worktree (required)

```
git worktree add ../f1-fantasy-7.2-scheduler -b chatgpt/7.2-scheduler main
```

All edits and commits happen in `../f1-fantasy-7.2-scheduler`. Claude works in parallel on task 7.1 in `../f1-fantasy-7.1-weekly` (`pipelines/weekly_update.py`, `tests/test_weekly_update.py`, `.gitignore`). Do NOT edit those files or anything under `pipelines/` or `src/`.

## Task 7.2

The command to schedule is fixed: `uv run python -m pipelines.weekly_update`, run from the project folder. It decides by itself whether a report is due (exits quickly otherwise), so the task simply runs it every day.

1. `scripts/install_task.ps1`:
   - Registers a scheduled task named `F1FantasyWeekly` with `Register-ScheduledTask` (no `schtasks` string parsing).
   - Trigger: daily at 20:00 local time.
   - Settings: `-StartWhenAvailable` (catch up after a missed start), run only when the user is logged on (no stored password, no highest privileges), stop if it runs longer than 1 hour.
   - Action: the full path of `uv.exe` resolved at install time with `(Get-Command uv).Source` (fail with a clear message if uv is not found), arguments `run python -m pipelines.weekly_update`, working directory = the repo root, derived from the script location (`Split-Path $PSScriptRoot -Parent`), never hardcoded.
   - Re-running the script replaces the existing task (`-Force`).
   - Prints the task name, next run time and the command.
2. `scripts/uninstall_task.ps1`: removes `F1FantasyWeekly` if present (`-Confirm:$false`), says so if absent.
3. `docs/how-it-works.md`: add a short "Weekly report" section: install/uninstall commands, that the report lands in `reports/round_{season}_{round}.md`, the run log in `reports/weekly_update.log`, `uv run python -m pipelines.weekly_update --force` for a manual rerun after editing team files, how to trigger a test run (`Start-ScheduledTask F1FantasyWeekly`), that the PC must be on and logged in, and that sealing `data/raw` stays manual.

Do not test by registering the task on the user's machine unless the user asks; check the scripts parse (`powershell -NoProfile -Command "[ScriptBlock]::Create((Get-Content scripts/install_task.ps1 -Raw)) | Out-Null"`). Run `uv run pytest -q` before committing; all tests must still pass.

## Deliverables

1. Commits on `chatgpt/7.2-scheduler` in the worktree (no push).
2. A short report to me: files changed, the parse check output, test count.
3. One dated line in `docs/progress.md`. Record any unfixed finding in `docs/known-issues.md`.
