
# Sentinel Edge source baseline v0.13.0

The immutable architecture baseline is stored in `docs/baseline/v0.13.0/`. The upstream manifest contains fifteen files: one docset README plus the fourteen architecture/specification documents indexed below. Hashes are SHA-256 over exact bytes.

| Source specification | SHA-256 | Bytes |
|---|---|---:|
| `sentinel-edge-module-01-streaming-source-collector-functional-v0.13.0.md` | `f655e8bb252d90f5691bd98c6870c4443b31f0ee015147c4644009f356558f4d` | 15459 |
| `sentinel-edge-module-01-streaming-source-collector-technical-v0.13.0.md` | `fc854097459889767e799b09b5e68c72785b3a41f2e9eaf40020532d654e5631` | 15934 |
| `sentinel-edge-module-02-analysis-enrichment-engine-functional-v0.13.0.md` | `a14f00d07464ab77f2d3b0ffb2183226bb86988bbd7035a04a0f31a293e23d1e` | 13072 |
| `sentinel-edge-module-02-analysis-enrichment-engine-technical-v0.13.0.md` | `91e23ecb8d04bfb31db1db1fbfbc005f3276805058932a21bf3cdc4cfac2603b` | 14477 |
| `sentinel-edge-module-03-model-workload-runtime-functional-v0.13.0.md` | `d95031eb9815f767d67f396db4236792147f3f0a441c8207bd19baa35f2d1219` | 12940 |
| `sentinel-edge-module-03-model-workload-runtime-technical-v0.13.0.md` | `9b704c5cb4b78660bf1190c23944302c9b1cd536855a8c5bce09d6b176c3c655` | 14379 |
| `sentinel-edge-module-04-incident-event-engine-functional-v0.13.0.md` | `00c89c3864db1c0a1ee8db1904ceb83553bf37a2d30e6d99a20f61c61ba08bf6` | 13107 |
| `sentinel-edge-module-04-incident-event-engine-technical-v0.13.0.md` | `ff8b354935c1744fc6a320b6a533f6f284cab4643f2dd609f67ed49dfd54f1f9` | 14506 |
| `sentinel-edge-module-05-rest-api-integration-gateway-functional-v0.13.0.md` | `fdf7cd8b2c596ebeb46e45573eb94611e590a3ffbe10aa440ee33448ab0413a7` | 13036 |
| `sentinel-edge-module-05-rest-api-integration-gateway-technical-v0.13.0.md` | `36c74de9bfd3e3cb7909f3f0040a8b942b201e0143d23853bec113fc5d4fe9ff` | 14347 |
| `sentinel-edge-module-06-client-applications-functional-v0.13.0.md` | `4082990defe04b5cbbca73a73e83d424a72e9dbd76a5c2b6d1418c024e66a683` | 13068 |
| `sentinel-edge-module-06-client-applications-technical-v0.13.0.md` | `4835759f00033d0d932efcd0bef3a3c97aa2a52e53a36330918cb2a1270498aa` | 14244 |
| `sentinel-edge-system-functional-architecture-v0.13.0.md` | `f511694f4d205fb7891d17fd0d46bb8f7ca0278de27c86ebecba3e882f995e19` | 15079 |
| `sentinel-edge-system-technical-architecture-integration-v0.13.0.md` | `1ecdff76430bd09481a4917550df2d6694a20e2146445fdd45c1086dffeafb82` | 19909 |

## Baseline invariants

- Six independently testable bounded modules.
- Incident & Event Engine is the sole incident lifecycle authority.
- Missing, stale, unhealthy, or incomplete data is never interpreted as safe.
- External low-trust evidence cannot independently verify, resolve, or mark an incident safe.
- Compact, isolated, and offline-field profiles preserve authoritative semantics.
- Physical and external-evidence slices plus whole-solution acceptance become permanent gates when activated.

Run `python scripts/validate_source_baseline.py` to verify every manifest entry, byte count, hash, and this exact fourteen-document index.
