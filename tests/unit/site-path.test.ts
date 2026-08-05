import { describe, expect, it } from "vitest";

import { normalizeBase, sitePath } from "../../src/lib/site-path";

describe("静态 base 路径", () => {
  it("根路径与子路径都保留尾斜杠、片段和数字路由", () => {
    expect(normalizeBase("/")).toBe("/");
    expect(normalizeBase("furuyoni-rules")).toBe("/furuyoni-rules/");
    expect(sitePath("/rules/core/05/#rule-5-8-3", "/")).toBe(
      "/rules/core/05/#rule-5-8-3",
    );
    expect(sitePath("/rules/core/05/#rule-5-8-3", "/furuyoni-rules/")).toBe(
      "/furuyoni-rules/rules/core/05/#rule-5-8-3",
    );
  });

  it("同时保留查询串和锚点", () => {
    expect(sitePath("/search/?q=樱#result", "/furuyoni-rules/")).toBe(
      "/furuyoni-rules/search/?q=樱#result",
    );
  });
});
