import fs from "node:fs";
import path from "node:path";

import { Snapshot, SnapshotSchema } from "@/lib/types";

// No backend server exists for this app (see docs/adr/0001) -- the analysis
// job commits data/snapshots/latest.json directly into the repo, and this
// reads it straight off disk at build time. A fresh deploy is how new data
// reaches the page; there is no runtime API call.
const SNAPSHOT_PATH = path.join(process.cwd(), "..", "data", "snapshots", "latest.json");

export function readSnapshot(): Snapshot {
  const raw = fs.readFileSync(SNAPSHOT_PATH, "utf-8");
  return SnapshotSchema.parse(JSON.parse(raw));
}
