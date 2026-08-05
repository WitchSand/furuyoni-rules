import MarkdownIt from "markdown-it";
import type { MarkdownIt as MarkdownItInstance, StateCore } from "markdown-it";

import type {
  GlossaryTerm,
  RulePart,
  SiteContent,
} from "./content-model";
import { ruleAnchor, stripInlineMarkup } from "./content-model";
import { sitePath } from "./site-path";

export type TermMarkerToken =
  | { kind: "text"; value: string }
  | { kind: "term"; display: string; termId: string };

export interface RenderRuleOptions {
  base: string;
  part: RulePart;
  content: SiteContent;
}

const termMarkerPattern = /\[\[([^\]|]+)\|([a-z0-9.-]+)\]\]/g;

const semanticTableCaptions: Readonly<Record<string, string>> = {
  "storm-force-wind": "风神量表：降低量与效果",
  "storm-force-thunder": "雷神量表：降低量与效果",
  "yatsuha-perfect-form": "完全态卡牌交换",
  "kanawe-act-colors": "当前幕颜色与效果",
  "kamuwi-taboo-gauge": "命与禁忌量表增量",
  "innealra-fate-positions": "女神与命运区位置",
};

function invariant(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(`正文渲染失败：${message}`);
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export function parseTermMarkers(
  source: string,
  glossaryById: ReadonlyMap<string, GlossaryTerm>,
): TermMarkerToken[] {
  const tokens: TermMarkerToken[] = [];
  let cursor = 0;
  for (const match of source.matchAll(termMarkerPattern)) {
    const index = match.index ?? 0;
    if (index > cursor) tokens.push({ kind: "text", value: source.slice(cursor, index) });
    const term = glossaryById.get(match[2]);
    invariant(term, `未知术语 ID ${match[2]}`);
    invariant(
      term.recommended_zh === match[1],
      `${match[2]} 必须显示锁定推荐名“${term.recommended_zh}”`,
    );
    tokens.push({ kind: "term", display: match[1], termId: match[2] });
    cursor = index + match[0].length;
  }
  if (cursor < source.length) tokens.push({ kind: "text", value: source.slice(cursor) });

  const markerStarts = (source.match(/\[\[/g) ?? []).length;
  const markerEnds = (source.match(/\]\]/g) ?? []).length;
  const parsedMarkers = tokens.filter((token) => token.kind === "term").length;
  invariant(
    markerStarts === markerEnds && markerStarts === parsedMarkers,
    "存在格式不完整的 [[显示文本|term-id]] 术语标记",
  );
  return tokens;
}

function renderTermMarkers(source: string, options: RenderRuleOptions): string {
  return parseTermMarkers(source, options.content.glossaryById)
    .map((token) => {
      if (token.kind === "text") return token.value;
      const href = sitePath(`/glossary/${token.termId}/`, options.base);
      return `<term-reference data-term-id="${escapeHtml(token.termId)}"><a class="term-link" href="${escapeHtml(href)}">${escapeHtml(token.display)}</a></term-reference>`;
    })
    .join("");
}

function renderContraptionLegend(): string {
  const entries = [
    ["attack", "攻击", "卡牌类型"],
    ["action", "行动", "卡牌类型"],
    ["enchantment", "付与", "卡牌类型"],
    ["reaction", "对应", "副类型"],
    ["full-power", "全力", "副类型"],
  ];
  return `<figure class="contraption-legend" aria-labelledby="contraption-legend-title">
  <figcaption id="contraption-legend-title">机巧图标文字图例（原创 CSS 图形）</figcaption>
  <ul>${entries
    .map(
      ([kind, label, group]) =>
        `<li><span class="contraption-icon contraption-icon--${kind}" aria-hidden="true"></span><strong>${label}</strong><small>${group}</small></li>`,
    )
    .join("")}</ul>
</figure>`;
}

function preprocessStructuralMarkers(source: string): string {
  const partLabels: Record<string, string> = {
    "front-matter": "封面与说明",
    core: "核心规则",
    additional: "追加规则",
    "appendix-1": "附则 1",
    "appendix-2": "附则 2",
  };
  return source
    .replace(
      /<!-- source-page: (\d+); printed-page: ([^;]+); part: ([^ ]+) -->/g,
      (_all, pdfPage: string, printedPage: string, part: string) => {
        const printed = printedPage.trim() === "null" ? "无印刷页码" : `印刷第 ${printedPage.trim()} 页`;
        return `\n<aside class="source-page-marker" id="source-page-${pdfPage}" data-source-page="${pdfPage}" data-pagefind-ignore aria-label="底本 PDF 第 ${pdfPage} 页，${printed}"><span>底本 PDF 第 ${pdfPage} 页</span><span>${printed}</span><span>${escapeHtml(partLabels[part] ?? part)}</span></aside>\n`;
      },
    )
    .replace(/<!-- \/source-page -->/g, "")
    .replace(
      /<!-- source-anomaly: ([^; ]+)([^>]*)-->/g,
      (_all, id: string, details: string) =>
        `\n<aside class="source-anomaly" data-pagefind-ignore><strong>源文异常标记</strong><code>${escapeHtml(id)}</code><span>${escapeHtml(details.replace(/^;\s*/, "").replaceAll(";", "；"))}</span></aside>\n`,
    )
    .replace(
      /<!-- original-graphic-replaced: contraption-icon-key; implementation: task-07-css-shapes-and-text -->/g,
      `\n${renderContraptionLegend()}\n`,
    );
}

function referenceMaps(content: SiteContent): {
  core: Map<string, string>;
  additional: Map<string, string>;
} {
  const build = (chapters: SiteContent["coreChapters"]) =>
    new Map(
      chapters.flatMap((chapter) =>
        chapter.ruleHeadings.map((heading) => [
          heading.number,
          `${chapter.route}#${heading.anchor}`,
        ]),
      ),
    );
  return { core: build(content.coreChapters), additional: build(content.additionalChapters) };
}

function installRuleReferencePlugin(
  markdown: MarkdownItInstance,
  options: RenderRuleOptions,
): void {
  const maps = referenceMaps(options.content);
  markdown.core.ruler.after("inline", "furuyoni-rule-references", (state: StateCore) => {
    for (let parentIndex = 0; parentIndex < state.tokens.length; parentIndex += 1) {
      const parent = state.tokens[parentIndex];
      if (parent.type !== "inline" || !parent.children) continue;
      if (state.tokens[parentIndex - 1]?.type === "heading_open") continue;

      let linkDepth = 0;
      const children = [];
      for (const child of parent.children) {
        if (child.type === "link_open" || child.type === "html_inline") linkDepth += 1;
        if (child.type !== "text" || linkDepth > 0) {
          children.push(child);
          if (child.type === "link_close" || child.type === "html_inline") linkDepth = Math.max(0, linkDepth - 1);
          continue;
        }

        let cursor = 0;
        for (const match of child.content.matchAll(/\d+(?:-\d+)+/g)) {
          const number = match[0];
          const index = match.index ?? 0;
          const prefix = child.content.slice(Math.max(0, index - 24), index);
          const preferred = /核心规则[^。；，\n]{0,18}$/.test(prefix)
            ? maps.core
            : /追加规则[^。；，\n]{0,18}$/.test(prefix)
              ? maps.additional
              : options.part === "additional"
                ? maps.additional
                : maps.core;
          const fallback = preferred === maps.core ? maps.additional : maps.core;
          const route = preferred.get(number) ?? fallback.get(number);
          if (!route) continue;
          if (index > cursor) {
            const text = new state.Token("text", "", 0);
            text.content = child.content.slice(cursor, index);
            children.push(text);
          }
          const open = new state.Token("link_open", "a", 1);
          open.attrSet("href", sitePath(route, options.base));
          open.attrSet("class", "rule-reference");
          const label = new state.Token("text", "", 0);
          label.content = number;
          const close = new state.Token("link_close", "a", -1);
          children.push(open, label, close);
          cursor = index + number.length;
        }
        if (cursor < child.content.length) {
          const text = new state.Token("text", "", 0);
          text.content = child.content.slice(cursor);
          children.push(text);
        }
      }
      parent.children = children;
    }
  });
}

function installSemanticTablePlugin(markdown: MarkdownItInstance): void {
  markdown.core.ruler.after("furuyoni-rule-references", "furuyoni-semantic-tables", (state: StateCore) => {
    const renderedTokens = [];
    let pendingTableId: string | undefined;
    let inSemanticTable = false;
    let inTableHead = false;
    let inTableBody = false;
    let firstBodyCell = false;
    let closingRowHeader = false;

    for (const token of state.tokens) {
      if (token.type === "html_block") {
        const declaration = token.content.match(
          /<!--\s*table:\s*rows=\d+;\s*columns=\d+;\s*id=([a-z0-9-]+)\s*-->/,
        );
        if (declaration) pendingTableId = declaration[1];
        else if (pendingTableId && /<table(?:\s|>)/.test(token.content)) pendingTableId = undefined;
        renderedTokens.push(token);
        continue;
      }

      if (token.type === "table_open" && pendingTableId) {
        const caption = semanticTableCaptions[pendingTableId];
        invariant(caption, `表格 ${pendingTableId} 缺少语义标题`);
        token.attrSet("data-table-id", pendingTableId);
        renderedTokens.push(token);
        const captionToken = new state.Token("html_block", "", 0);
        captionToken.content = `<caption>${escapeHtml(caption)}</caption>\n`;
        renderedTokens.push(captionToken);
        pendingTableId = undefined;
        inSemanticTable = true;
        continue;
      }

      if (inSemanticTable) {
        if (token.type === "thead_open") inTableHead = true;
        if (token.type === "thead_close") inTableHead = false;
        if (token.type === "tbody_open") inTableBody = true;
        if (token.type === "tbody_close") inTableBody = false;
        if (token.type === "tr_open" && inTableBody) firstBodyCell = true;
        if (token.type === "th_open" && inTableHead) token.attrSet("scope", "col");
        if (token.type === "td_open" && inTableBody && firstBodyCell) {
          token.type = "th_open";
          token.tag = "th";
          token.attrSet("scope", "row");
          firstBodyCell = false;
          closingRowHeader = true;
        } else if (token.type === "td_open" && inTableBody) {
          firstBodyCell = false;
        }
        if (token.type === "td_close" && closingRowHeader) {
          token.type = "th_close";
          token.tag = "th";
          closingRowHeader = false;
        }
        if (token.type === "table_close") inSemanticTable = false;
      }

      renderedTokens.push(token);
    }
    state.tokens = renderedTokens;
  });
}

export function renderRuleMarkdown(source: string, options: RenderRuleOptions): string {
  const markdown = new MarkdownIt({ html: true, linkify: false, typographer: false });
  installRuleReferencePlugin(markdown, options);
  installSemanticTablePlugin(markdown);
  markdown.renderer.rules.heading_open = (tokens, index, rendererOptions) => {
    const token = tokens[index];
    const inline = tokens[index + 1]?.content ?? "";
    const plain = stripInlineMarkup(inline);
    const rule = plain.match(/^(\d+(?:-\d+)+)\b/);
    const chapter = plain.match(/^§(\d+)\b/);
    const id = rule ? ruleAnchor(rule[1]) : chapter ? `chapter-${chapter[1]}` : undefined;
    if (id) token.attrSet("id", id);
    token.attrSet("tabindex", "-1");
    return markdown.renderer.renderToken(tokens, index, rendererOptions);
  };

  const withTerms = renderTermMarkers(source, options);
  const prepared = preprocessStructuralMarkers(withTerms);
  return markdown.render(prepared);
}
