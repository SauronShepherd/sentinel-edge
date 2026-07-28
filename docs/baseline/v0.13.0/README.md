# Sentinel Edge v0.13.0 Modular Documentation Set

Date: 2026-07-26

## Requested document pairs

- High-level system pair: functional architecture + technical architecture/integration.
- Six module pairs: functional product specification + technical architecture/specification for each module.

## Files

- [sentinel-edge-system-functional-architecture-v0.13.0.md](sentinel-edge-system-functional-architecture-v0.13.0.md)
- [sentinel-edge-system-technical-architecture-integration-v0.13.0.md](sentinel-edge-system-technical-architecture-integration-v0.13.0.md)
- [sentinel-edge-module-01-streaming-source-collector-functional-v0.13.0.md](sentinel-edge-module-01-streaming-source-collector-functional-v0.13.0.md)
- [sentinel-edge-module-01-streaming-source-collector-technical-v0.13.0.md](sentinel-edge-module-01-streaming-source-collector-technical-v0.13.0.md)
- [sentinel-edge-module-02-analysis-enrichment-engine-functional-v0.13.0.md](sentinel-edge-module-02-analysis-enrichment-engine-functional-v0.13.0.md)
- [sentinel-edge-module-02-analysis-enrichment-engine-technical-v0.13.0.md](sentinel-edge-module-02-analysis-enrichment-engine-technical-v0.13.0.md)
- [sentinel-edge-module-03-model-workload-runtime-functional-v0.13.0.md](sentinel-edge-module-03-model-workload-runtime-functional-v0.13.0.md)
- [sentinel-edge-module-03-model-workload-runtime-technical-v0.13.0.md](sentinel-edge-module-03-model-workload-runtime-technical-v0.13.0.md)
- [sentinel-edge-module-04-incident-event-engine-functional-v0.13.0.md](sentinel-edge-module-04-incident-event-engine-functional-v0.13.0.md)
- [sentinel-edge-module-04-incident-event-engine-technical-v0.13.0.md](sentinel-edge-module-04-incident-event-engine-technical-v0.13.0.md)
- [sentinel-edge-module-05-rest-api-integration-gateway-functional-v0.13.0.md](sentinel-edge-module-05-rest-api-integration-gateway-functional-v0.13.0.md)
- [sentinel-edge-module-05-rest-api-integration-gateway-technical-v0.13.0.md](sentinel-edge-module-05-rest-api-integration-gateway-technical-v0.13.0.md)
- [sentinel-edge-module-06-client-applications-functional-v0.13.0.md](sentinel-edge-module-06-client-applications-functional-v0.13.0.md)
- [sentinel-edge-module-06-client-applications-technical-v0.13.0.md](sentinel-edge-module-06-client-applications-technical-v0.13.0.md)

## Design result

Each module is independently packageable, starts with fake ports, owns its persistence, publishes versioned contracts, provides plugin conformance fixtures, and participates in pairwise, vertical-slice and whole-solution tests.

## Current source/research registry

The Collector pair owns source-policy/open-data details; the high-level technical document records the current research consequences and standards baseline.
