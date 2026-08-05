import { describe, expect, it } from "vitest";

import { loadSiteContent } from "../../src/lib/content-model";
import {
  additionalChapterGoddess,
  buildGlossarySearchText,
  normalizeSearchText,
  termGoddessFilters,
} from "../../src/lib/search-normalization";

describe("搜索规范化", () => {
  const content = loadSiteContent();

  it("统一全角、大小写、空白和卡号分隔符", () => {
    expect(normalizeSearchText(" ＮＡ－１０－KURURU－A1－S－3－Ex1 ")).toBe(
      "na-10-kururu-a1-s-3-ex1",
    );
  });

  it("术语搜索文本同时包含推荐简中、日文原词与社区别名", () => {
    const term = content.glossaryById.get("game.shinmaku");
    expect(term).toBeDefined();
    const text = buildGlossarySearchText(term!);
    expect(text).toContain("散樱乱武 新幕");
    expect(text).toContain("新幕 桜降る代に決闘を");
    expect(text).toContain("新幕散樱乱武");
  });

  it("从追加规则锚点生成稳定的女神筛选值", () => {
    const term = content.glossaryById.get("mechanic.kururu.contraption");
    expect(term).toBeDefined();
    expect(termGoddessFilters(term!, content)).toContain("枢");
    expect(additionalChapterGoddess(24, content)).toBe("伊尼尔");
    expect(additionalChapterGoddess(2, content)).toBeUndefined();
  });
});
