export type Hazard = "wildfire" | "earthquake" | "flood" | "landslide";
export type HazardState = "unknown" | "normal" | "watch" | "alert" | "degraded";

export type SemanticIncident = {
  hazard: Hazard;
  state: HazardState;
  trust: { freshness: string; source: string; clock: string };
  permissions: { canAcknowledge: boolean; canReview: boolean };
  safetyWording: string;
  commands: readonly string[];
};

export const semanticIncident = (hazard: Hazard, state: HazardState): SemanticIncident => ({
  hazard,
  state,
  trust: { freshness: "fresh", source: "observed", clock: "trusted" },
  permissions: { canAcknowledge: false, canReview: true },
  safetyWording: "Research monitoring and decision support; not an official warning service.",
  commands: ["acknowledge", "review", "export"],
});

export const semanticSurfaceFields = (incident: SemanticIncident): readonly string[] => [
  incident.hazard,
  incident.state,
  incident.trust.freshness,
  incident.trust.source,
  incident.trust.clock,
  String(incident.permissions.canAcknowledge),
  String(incident.permissions.canReview),
  incident.safetyWording,
  ...incident.commands,
];
