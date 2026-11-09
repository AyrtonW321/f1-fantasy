# F1 Fantasy Optimizer

Python system that reproduces official F1 Fantasy scoring for 2023-2026, predicts fantasy points, and picks the optimal team each round under the budget cap. Target: backtest on 2023-2026, live for Round 1 of 2027.

- Spec: docs/superpowers/specs/2026-11-09-f1-fantasy-optimizer.md (Part 1 overrides Part 2)
- Plan: docs/superpowers/plans/2026-11-09-f1-fantasy-optimizer.md

## Roles

- You (the main session) are the orchestrator. You plan, write briefs and check results. You don't do bulk work yourself when a worker can.
- Workers are subagents on Haiku: `builder` and `reviewer` in .claude/agents/.
- Every brief states the goal, the files to read, and a "Done when:" check that can be run or seen.
- Before accepting any worker's output, run its check yourself. If it fails, send it back with the failure. Never pass on a worker's report unchecked.

## Session routine

- Start: read this file and docs/progress.md, docs/decisions.md, docs/known-issues.md.
- End: update progress.md (including one dated log line), add new decisions (date and why) and gotchas, run the `reflect` skill and propose skill edits with this session's evidence. The user approves before you apply them.

## Hard rules (copy into every brief that touches them)

- No phase starts before the previous phase's acceptance passes.
- Game rules live in config/rules_{season}.yaml, never in code. A `null` value raises UnknownRuleError; never fill one in to pass a test. If the scoring gate fails on real data, stop and report the rows.
- Every feature row has `known_at`. Nothing uses data after that round's `lock_utc`.
- Never read TracingInsights `priceChange` (post-race data).
- Ask before adding a dependency the spec doesn't list.
- No plaintext data in git: real data is committed only as data/raw.tar.gz.enc. Never commit, log or print F1_DATA_KEY.
- Before the first commit run `git rev-parse --show-toplevel`; it must print this project folder.
- Pushes and repo changes need the user's OK. Workers never commit or push.

## Folder map (planned unless it exists)

```
config/         rules_2023..2026.yaml, model.yaml
data/           raw.tar.gz.enc (committed); raw/ and processed/ (gitignored)
docs/           progress.md, decisions.md, known-issues.md, superpowers/{specs,plans}
pipelines/      build_data.py
reports/
src/ingest/     vault, fantasy_scrape, community_pull, jolpica_pull, build_tables, ti_lines, crosscheck
src/sim/        scoring.py
src/features/   rolling.py, guard.py
src/optimize/   ilp.py
src/backtest/   walkforward.py
tests/
.claude/        agents/{builder,reviewer}.md, skills/reflect/SKILL.md
```
