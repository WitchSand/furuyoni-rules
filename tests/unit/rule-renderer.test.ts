import { describe, expect, it } from "vitest";

import { loadSiteContent } from "../../src/lib/content-model";
import { parseTermMarkers, renderRuleMarkdown } from "../../src/lib/rule-renderer";

describe("规则正文渲染器", () => {
  const content = loadSiteContent();

  it("把锁定术语标记渲染为无 JavaScript 也可访问的链接", () => {
    expect(parseTermMarkers("使用[[樱花结晶|object.sakura-crystal]]。", content.glossaryById)).toEqual([
      { kind: "text", value: "使用" },
      { kind: "term", display: "樱花结晶", termId: "object.sakura-crystal" },
      { kind: "text", value: "。" },
    ]);

    const html = renderRuleMarkdown("使用[[樱花结晶|object.sakura-crystal]]。", {
      base: "/furuyoni-rules/",
      part: "core",
      content,
    });
    expect(html).toContain('data-term-id="object.sakura-crystal"');
    expect(html).toContain('href="/furuyoni-rules/glossary/object.sakura-crystal/"');
  });

  it("保留页码、规则锚点、修订文字标签、异常标记与原创机巧图例", () => {
    const html = renderRuleMarkdown(
      `<!-- source-page: 45; printed-page: null; part: additional -->

### 8-2 机巧

<span data-revision="2025-04-25-update">修订（2025-04-25 更新）</span>

<!-- source-anomaly: p47-transform-spelling; handling: preserved -->

<!-- original-graphic-replaced: contraption-icon-key; implementation: task-07-css-shapes-and-text -->

<!-- /source-page -->`,
      { base: "/", part: "additional", content },
    );
    expect(html).toContain('id="source-page-45"');
    expect(html).toContain('id="rule-8-2"');
    expect(html).toContain("2025-04-25 更新");
    expect(html).toContain("源文异常标记");
    for (const label of ["攻击", "行动", "付与", "对应", "全力"]) {
      expect(html).toContain(label);
    }
  });

  it("将已知规则编号解析为当前规则分部的稳定数字路由", () => {
    const html = renderRuleMarkdown("依照 5-8-3 结算。", {
      base: "/",
      part: "core",
      content,
    });
    expect(html).toContain('href="/rules/core/05/#rule-5-8-3"');
  });

  it("把已声明的 Markdown 表格渲染为带标题及行列标题的语义表格", () => {
    const html = renderRuleMarkdown(
      `<!-- table: rows=4; columns=2; id=storm-force-wind -->

| 降低量 | 效果 |
| --- | --- |
| 1 | 距离⇔虚：1 |
| 2 | 抽取 1 张卡牌。 |
| 3 | 获得 1 点集中力。 |`,
      { base: "/", part: "additional", content },
    );

    expect(html).toContain("<caption>风神量表：降低量与效果</caption>");
    expect(html).toContain('<th scope="col">降低量</th>');
    expect(html).toContain('<th scope="row">1</th>');
  });

  it("拒绝未知、改名或残缺的术语标记", () => {
    expect(() => parseTermMarkers("[[未知|term.missing]]", content.glossaryById)).toThrow("未知术语 ID");
    expect(() => parseTermMarkers("[[樱花晶体|object.sakura-crystal]]", content.glossaryById)).toThrow("锁定推荐名");
    expect(() => parseTermMarkers("[[樱花结晶|object.sakura-crystal]", content.glossaryById)).toThrow("格式不完整");
  });
});
