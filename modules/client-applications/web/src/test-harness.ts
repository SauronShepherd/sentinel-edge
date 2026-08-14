export function createWebHarness() { return { online: false, source: "generated-mock" }; }
import { semanticIncident, semanticSurfaceFields } from "../../shared-domain/src/semantic-contract.ts";

export const webSemanticSurface = semanticSurfaceFields(semanticIncident("wildfire", "watch"));
