export function createMobileHarness() { return { device: "fake", notifications: false }; }
import { semanticIncident, semanticSurfaceFields } from "../../shared-domain/src/semantic-contract.ts";

export const mobileSemanticSurface = semanticSurfaceFields(semanticIncident("wildfire", "watch"));
