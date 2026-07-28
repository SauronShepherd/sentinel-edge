// Static boundary fixture: client code may depend on contracts, never server internals.
const forbidden = ["sqlite", "fs", "sentinel_incident_event_engine", "internal-transport"];
if (forbidden.some((name) => name.includes("sentinel_incident_event_engine"))) {
  throw new Error("client boundary fixture loaded");
}
