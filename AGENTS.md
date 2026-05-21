# Isaac Sim — Agent Guide

At the start of every conversation, read the following in full to load all project rules and skills:

- All `SKILL.md` files anywhere under `skills/`. Use a traversal that includes every nested directory even when search tools would normally skip ignored paths, for example:
  ```bash
  find skills -type f -name SKILL.md -print
  ```

`skills/` is the canonical, agent-agnostic location for SKILL.md-format workflow guides.

Cursor and Claude Code load the same skills via their respective pointer mechanisms (`.cursor/rules/agent_skills.mdc`, `CLAUDE.md`). For Codex (this file), the skills are background context — refer to them when the user's task overlaps a skill's subject.
