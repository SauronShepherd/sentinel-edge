
# ADR-0004: Default implementation profile

- Status: Accepted
- Date: 2026-07-26

## Selected profile

| Concern | Default |
|---|---|
| Backend | Python 3.12/3.13, typed ports, asyncio-compatible application services |
| Packaging/workspace | `uv`, PEP 621 packages, immutable lock and content digests |
| Persistence | SQLite with WAL, per-module databases, explicit migrations |
| Compact transport | Bounded in-memory queues behind transport-neutral ports |
| Isolated transport | Versioned framed messages over Unix domain sockets, planned for I15 |
| Contracts | JSON Schema 2020-12, CloudEvents-compatible envelopes, AsyncAPI, OpenAPI 3.1 |
| Web | TypeScript responsive PWA |
| Mobile | TypeScript shared domain plus a replaceable native shell |
| Tests | pytest, property/state-machine tests, generated contracts, signed scenarios |
| CI | GitHub Actions, Linux x86_64 fast/full lanes and Linux Arm64 qualification lane |
| Target | Linux Arm64; target hardware and benchmark protocol become release-blocking in I18 |

## I00 bootstrap constraint

I00 has no runtime dependency. The lock therefore contains only the virtual workspace. Governance tools use Python standard-library implementations; CI provisions pinned optional validators when available. Module dependencies become independently locked when their packages activate.

## Consequences

The repository starts offline and deterministically, supports SQLite and Arm64 from the beginning, and avoids binding domain code to deployment transport. Web/mobile and generated contract tooling are activated only in their planned iterations.
