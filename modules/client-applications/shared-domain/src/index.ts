export type LifecycleState = "starting" | "ready" | "degraded" | "draining" | "stopped";
export type ModulePort = { name: string; state: LifecycleState };
