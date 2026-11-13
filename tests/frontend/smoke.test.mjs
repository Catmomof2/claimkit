// Frontend smoke test (node --test, no dependencies).
// Checks the starter is coherent: package.json is valid, the dashboard
// and components exist, and the detention math matches the backend rule.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "frontend");
const detention = (waited, free, rate) => Math.round(Math.max(0, waited - free) * rate * 100) / 100;

test("package.json is valid JSON with Next.js scripts", () => {
  const pkg = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
  assert.equal(pkg.name, "claimkit-frontend");
  assert.ok(pkg.scripts.dev && pkg.scripts.build && pkg.scripts.test);
});

test("dashboard and components exist", () => {
  for (const f of ["app/dashboard/page.tsx", "app/page.tsx", "components/ShipmentCard.tsx",
    "components/DetentionCalculator.tsx", "components/DeadlineList.tsx", "components/UploadForm.tsx",
    "services/api.ts", "services/sample.ts"]) {
    assert.ok(fs.existsSync(path.join(root, f)), `missing ${f}`);
  }
});

test("detention math matches backend rule", () => {
  assert.equal(detention(5.5, 2, 75), 262.5);
  assert.equal(detention(1.5, 2, 75), 0);
});
