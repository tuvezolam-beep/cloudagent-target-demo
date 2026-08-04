# Repository guidance for coding agents

## Scope

- Treat this repository as a production-like API, even though it uses an in-memory store.
- Preserve existing endpoint contracts unless the assigned task explicitly changes them.
- Prefer the smallest change that completely satisfies the task.
- Do not edit `grader_tests/` to make a task pass.

## Required verification

Before reporting completion:

1. Add or update a public regression test in `tests/`.
2. Run `pytest`.
3. Run the task-specific acceptance test when it is available.
4. Run `ruff check app tests`.
5. Report any residual risk instead of silently ignoring it.

## Pull requests

- Use `fix/<task-id>-<slug>` for fixes and `feat/<task-id>-<slug>` for features.
- Keep unrelated refactors out of the task branch.
- Include the root cause or design rationale, test evidence, and rollback notes in the PR body.

