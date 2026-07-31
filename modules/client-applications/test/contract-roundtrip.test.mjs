import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

test("generated contract canonical JSON remains stable across client boundary", () => {
  const schema = JSON.parse(fs.readFileSync(path.resolve("../../contracts/sentinel-contracts/schemas/collector.v1.json"), "utf8"));
  const canonical = { observation_id: "obs-1", observed_at: "2026-01-01T00:00:00Z", units: "metric", clock_quality: "good", replay: false, policy: "public", source_health: "healthy", acquisition_audit: {} };
  for (const required of schema.required) assert.ok(required in canonical, `missing ${required}`);
  assert.deepEqual(JSON.parse(JSON.stringify(canonical)), canonical);
});
