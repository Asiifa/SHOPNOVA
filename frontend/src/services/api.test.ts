import { describe, expect, it } from "vitest";
import { inr } from "@/services/api";

describe("inr formatter", () => {
  it("formats Indian Rupees", () => {
    expect(inr(2499)).toBe("₹2,499");
    expect(inr(0)).toBe("₹0");
    expect(inr(123456)).toBe("₹1,23,456");
  });
});
