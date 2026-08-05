import type { GlossaryAnchor, SiteContent } from "./content-model";
import { sitePath } from "./site-path";

export const categoryLabels: Record<string, string> = {
  project_concept: "项目与对局概念",
  region_resource: "区域与资源",
  card_type: "卡牌与类型",
  effect_class: "效果分类",
  phase_action: "阶段与动作",
  rule_keyword: "规则关键词",
  goddess: "女神",
  goddess_mechanism: "女神机制",
};

export const confidenceLabels: Record<string, string> = {
  high: "高",
  medium: "中",
  low: "低",
};

export const evidenceLevelLabels: Record<number, string> = {
  0: "规则底本",
  1: "一级",
  2: "二级",
  3: "三级",
  4: "四级",
};

export const sourceAccessibilityLabels: Record<string, string> = {
  accessible: "可访问",
  "accessible-with-gaps": "可访问，但存在内容缺口",
  "indexed-snapshot-only": "仅有索引快照",
  "intermittent-indexed-snapshot": "间歇可访问，以索引快照为主",
};

export function glossaryAnchorHref(
  anchor: GlossaryAnchor,
  content: SiteContent,
  base: string,
): string {
  const ruleNumber = anchor.rule?.match(/\d+(?:-\d+)+/)?.[0];
  const chapterNumber = ruleNumber?.split("-")[0];
  let route: string;
  if (anchor.part === "core" && chapterNumber) {
    route = content.coreChapters.find((chapter) => chapter.number === Number(chapterNumber))?.route
      ?? `/rules/core/${chapterNumber.padStart(2, "0")}/`;
  } else if (anchor.part === "additional" && chapterNumber) {
    route = content.additionalChapters.find((chapter) => chapter.number === Number(chapterNumber))?.route
      ?? `/rules/additional/${chapterNumber.padStart(2, "0")}/`;
  } else if (anchor.part === "appendix-1") {
    route = "/rules/appendix/01/";
  } else if (anchor.part === "appendix-2") {
    route = "/rules/appendix/02/";
  } else {
    route = "/rules/front/";
  }
  const fragment = ruleNumber ? `#rule-${ruleNumber}` : `#source-page-${anchor.pdf_page}`;
  return sitePath(`${route}${fragment}`, base);
}

export function partLabel(part: string): string {
  return {
    core: "核心规则",
    additional: "追加规则",
    "appendix-1": "附则 1 · 女神列表",
    "appendix-2": "附则 2 · 勘误",
    "front-matter": "封面与说明",
  }[part] ?? part;
}
