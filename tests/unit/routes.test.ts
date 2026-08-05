import { describe, expect, it } from "vitest";

import { loadSiteContent } from "../../src/lib/content-model";
import { glossaryAnchorHref } from "../../src/lib/routes";

const content = loadSiteContent();

describe("术语规则定位", () => {
  it("从带段落说明的核心规则锚点提取稳定编号", () => {
    expect(
      glossaryAnchorHref({ part: "core", pdf_page: 20, rule: "8-2-2 A" }, content, "/"),
    ).toBe("/rules/core/08/#rule-8-2-2");
  });

  it("范围锚点定位到起始规则并带入子路径基址", () => {
    expect(
      glossaryAnchorHref(
        { part: "additional", pdf_page: 39, rule: "3-2 至 3-3" },
        content,
        "/furuyoni-rules/",
      ),
    ).toBe("/furuyoni-rules/rules/additional/03/#rule-3-2");
  });

  it("附则的描述性锚点回退到可访问的底本页锚点", () => {
    expect(
      glossaryAnchorHref(
        { part: "appendix-1", pdf_page: 75, rule: "附则1 女神列表" },
        content,
        "/",
      ),
    ).toBe("/rules/appendix/01/#source-page-75");
  });
});
