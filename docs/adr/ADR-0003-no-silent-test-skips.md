
# ADR-0003: No silent test skips or flaky completion evidence

- Status: Accepted
- Date: 2026-07-26

## Decision

Capabilities are `planned`, `active`, `demonstrated`, or `retired`. Only active capabilities contribute mandatory suites. Planned lanes may report their state but cannot be counted as passing test evidence.

A release or iteration gate fails on:

- skipped or xfailed tests;
- deselection or collection errors;
- retry/rerun-based success;
- missing active acceptance tests or evidence paths;
- stale evidence or generated artifacts.

A failing test is classified, preserved, reproduced, and fixed through one-primary-file remediation tasks. Converting it to skip, xfail, warning suppression, or retry is not completion evidence. Any change to code, configuration, fixtures, dependencies, models, or environment invalidates affected evidence and requires the full gate to rerun.

## Enforcement

`check_no_silent_skips.py` scans JUnit XML and terminal logs. The I00 gate includes controlled failure and skip proofs. CI uploads reports even when jobs fail, and the aggregate job depends on all active lanes.
