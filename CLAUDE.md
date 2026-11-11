# F1 Fantasy Optimizer

Python system. Reproduce official F1 Fantasy scoring 2023-2026, predict fantasy points, pick optimal team each round under budget cap. Target: backtest on 2023-2026, live for Round 1 of 2027.

- Spec: docs/superpowers/specs/2026-11-09-f1-fantasy-optimizer.md (Part 1 overrides Part 2)
- Plan: docs/superpowers/plans/2026-11-09-f1-fantasy-optimizer.md

## Session routine

- Start: read this file and docs/progress.md, docs/decisions.md, docs/known-issues.md.
- End: update progress.md (include one dated log line), add new decisions (date and why) and gotchas, record unfixed review findings in known-issues.md, run `reflect` skill, propose skill edits with this session's evidence. User approves before you apply.

## Code style: ponytail

Use ponytail (full) on all coding tasks here: lazy senior dev, laziest solution that works. Reuse existing helper, stdlib, installed dep before new code. Shortest correct diff. Non-trivial logic leaves one runnable check.

## Hard rules

- No phase starts before previous phase's acceptance passes.
- Game rules live in config/rules_{season}.yaml, never in code. `null` value raises UnknownRuleError; never fill one in to pass test. Scoring gate fails on real data: stop, report rows.
- Every feature row has `known_at`. Nothing uses data after that round's `lock_utc`.
- Never read TracingInsights `priceChange` (post-race data).
- Ask before adding dependency spec doesn't list.
- No plaintext data in git: real data committed only as data/raw.tar.gz.enc. Never commit, log or print F1_DATA_KEY.
- Before first commit run `git rev-parse --show-toplevel`; must print this project folder.
- Pushes and repo changes need user's OK.

## Folder map (planned unless it exists)

```
config/         rules_2023..2026.yaml, model.yaml
data/           raw.tar.gz.enc (committed); raw/ and processed/ (gitignored)
docs/           progress.md, decisions.md, known-issues.md, superpowers/{specs,plans}
graphify-out/   graph.json, GRAPH_REPORT.md, graph.html (committed); cache/ (gitignored). Tool: uv tool install graphifyy
pipelines/      build_data.py
reports/
src/ingest/     vault, fantasy_scrape, community_pull, jolpica_pull, build_tables, ti_lines, crosscheck
src/sim/        scoring.py
src/features/   rolling.py, guard.py
src/optimize/   ilp.py
src/backtest/   walkforward.py
tests/
.claude/        skills/reflect/SKILL.md
```

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.
