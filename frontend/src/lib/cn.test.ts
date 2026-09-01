// File: frontend/src/lib/cn.test.ts
import { describe, expect, it } from "vitest";

import { cn } from "./cn";

describe("cn", () => {
  it("merges static classes", () => {
    expect(cn("a", "b")).toBe("a b");
  });

  it("strips falsy", () => {
    expect(cn("a", false, undefined, null, "b")).toBe("a b");
  });

  it("merges Tailwind class collisions", () => {
    expect(cn("p-2", "p-4")).toBe("p-4");
  });
});
