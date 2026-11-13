import { describe, expect, it } from "vitest";
import { discountPercent } from "@/utils/format";

describe("discountPercent", () => {
  it("returns null when there is no discount", () => {
    expect(discountPercent(1000)).toBeNull();
    expect(discountPercent(1000, 1000)).toBeNull();
    expect(discountPercent(1000, 1100)).toBeNull();
  });

  it("computes the discount percentage", () => {
    expect(discountPercent(3499, 2499)).toBe(29);
    expect(discountPercent(1000, 500)).toBe(50);
  });
});
