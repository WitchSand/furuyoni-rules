import { describe, expect, it } from "vitest";

import { loadSiteContent } from "../../src/lib/content-model";
import {
  additionalChapterGoddess,
  buildGlossarySearchText,
  glossaryTermMatchesQuery,
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

  it("2026-08-29 修订项使用新推荐名并保留旧译检索", () => {
    const revisions = [
      ["zone.attack-in-progress", "攻击中区", "攻击中"],
      ["goddess.21", "卡姆伊", "神居"],
      ["goddess.24", "西斯伊", "志水"],
      ["goddess.nonselectable.kodama", "科达玛", "菰珠"],
      ["goddess.nonselectable.zanka", "赞卡", "斩华"],
      ["goddess.nonselectable.wouka", "沃卡", "奥华"],
    ] as const;

    for (const [id, previousName, currentName] of revisions) {
      const term = content.glossaryById.get(id);
      expect(term).toBeDefined();
      expect(term!.recommended_zh).toBe(currentName);
      expect(term!.aliases).toContain(previousName);
      expect(term!.aliases).not.toContain(currentName);
      expect(new Set(term!.aliases).size).toBe(term!.aliases.length);
      expect(buildGlossarySearchText(term!)).toContain(previousName);
      expect(buildGlossarySearchText(term!)).toContain(currentName);
      expect(glossaryTermMatchesQuery(term!, previousName)).toBe(true);
      expect(glossaryTermMatchesQuery(term!, currentName)).toBe(true);
    }
  });

  it("从追加规则锚点生成稳定的女神筛选值", () => {
    const term = content.glossaryById.get("mechanic.kururu.contraption");
    expect(term).toBeDefined();
    expect(termGoddessFilters(term!, content)).toContain("枢");
    expect(additionalChapterGoddess(24, content)).toBe("伊尼尔");
    expect(additionalChapterGoddess(2, content)).toBeUndefined();
  });
});
