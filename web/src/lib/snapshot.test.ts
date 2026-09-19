import { describe, expect, it } from "vitest";

import { readSnapshot } from "@/lib/snapshot";

describe("readSnapshot", () => {
  it("parses the real committed snapshot without schema drift", () => {
    const snapshot = readSnapshot();

    expect(snapshot.squad.length).toBeGreaterThan(0);
    expect(snapshot.schema_version).toBe(1);
  });
});
