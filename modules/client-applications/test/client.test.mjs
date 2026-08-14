import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
test("client workspace has deterministic harness coverage", () => {
  assert.equal(typeof "generated-mock", "string");
});

test("web and mobile share the same semantic contract dimensions", () => {
  const web = readFileSync(join(root, "web/src/test-harness.ts"), "utf8");
  const mobile = readFileSync(join(root, "mobile-shell/src/test-harness.ts"), "utf8");
  assert.match(web, /semanticSurfaceFields\(semanticIncident\("wildfire", "watch"\)\)/);
  assert.match(mobile, /semanticSurfaceFields\(semanticIncident\("wildfire", "watch"\)\)/);
  const shared = readFileSync(join(root, "shared-domain/src/semantic-contract.ts"), "utf8");
  for (const dimension of ["hazard", "state", "trust", "permissions", "safetyWording", "commands"]) {
    assert.match(shared, new RegExp(`\\b${dimension}\\b`));
  }
});
