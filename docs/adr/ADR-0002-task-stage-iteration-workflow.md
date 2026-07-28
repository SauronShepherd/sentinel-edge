
# ADR-0002: Atomic task, stage, and gated iteration workflow

- Status: Accepted
- Date: 2026-07-26

## Decision

A task changes exactly one primary file. A stage groups related tasks across files to deliver one coherent outcome. An iteration groups stages into a capability increment and remains incomplete until its complete regression gate is green.

Every behavior-changing task should first create or strengthen the narrowest failing test. A fix that needs another file creates another task in the same stage. Generated output and drift verification are separate tasks.

## Example

A two-file change is invalid as one task:

```text
INVALID: update incident policy and its API projection in one task.
```

It is split instead:

```text
T01 primary file: modules/incident/.../policy.py
T02 primary file: modules/api/.../projection.py
Stage verification: real producer/consumer contract test
```

## Iteration state

`planned -> in-progress -> implementation-complete -> gate-running -> blocked|complete`

Any failure, skip, xfail, collection error, flaky rerun, or stale evidence moves the iteration to `blocked`. After any input changes, targeted checks run first, then stage checks, then the complete iteration gate from its first step.
