export type LifecycleState = "starting" | "ready" | "degraded" | "draining" | "stopped";
export type ModulePort = { name: string; state: LifecycleState };
export type { AnalyzerV1, ApiV1, CollectorV1, IncidentV1, RuntimeV1 } from "../../../../contracts/generated/typescript_bindings";
