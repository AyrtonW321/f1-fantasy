---
name: reflect
description: End-of-session review. Lists what went wrong or took too long, proposes the smallest edit to CLAUDE.md, an agent file or a skill that would have prevented it, and waits for approval. Use at the end of a session or when the user says "reflect".
---

# Reflect

1. List what went wrong or took too long this session: failed worker checks, rework loops, wrong assumptions, repeated questions, anything the user corrected. Cite the evidence for each (command, output or message). If nothing went wrong, say so; don't invent problems.
2. For each item, name the repeatable cause. Drop one-offs.
3. Propose the smallest edit that would have prevented it, to CLAUDE.md, a file in .claude/agents/, or a skill in .claude/skills/. Show exact replacement text with the evidence beside it. One edit per problem. No new files or broad rewrites.
4. Stop and wait for the user's OK. Apply only the edits they approve.
