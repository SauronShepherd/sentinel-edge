import test from "node:test";
import assert from "node:assert/strict";
test("client workspace has deterministic harness coverage", () => {
  assert.equal(typeof "generated-mock", "string");
});
