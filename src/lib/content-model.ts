import { readFileSync } from "node:fs";
import { resolve } from "node:path";

export const SOURCE_PDF_SHA256 =
  "b96c743b343d7522db61af03952db73189283816868b8e8747f289a71801ab98";

export type RulePart =
  | "front-matter"
  | "core"
  | "additional"
  | "appendix-1"
  | "appendix-2";

export type Confidence = "high" | "medium" | "low";

export interface GlossaryAnchor {
  part: string;
  pdf_page: number;
  rule?: string;
}

export interface GlossaryTerm {
  id: string;
  category: string;
  recommended_zh: string;
  ja: string;
  aliases: string[];
  strict_definition: string;
  plain_explanation: string;
  anchors: GlossaryAnchor[];
  evidence: Array<{ source_id: string; role: string }>;
  confidence: Confidence;
  review_status: "locked";
  impact: "high" | "medium" | "low";
  conflict_note: string;
}

export interface GlossarySource {
  id: string;
  kind: string;
  evidence_level: number;
  title: string;
  url: string;
  accessed_at: string;
  accessibility: string;
  evidence_summary: string;
  limitations: string;
}

export interface RuleHeading {
  level: number;
  number: string;
  title: string;
  anchor: string;
}

export interface SourcePage {
  pdfPage: number;
  printedPage: number | null;
  part: RulePart;
  markdown: string;
  ruleHeadings: RuleHeading[];
  termIds: string[];
  cardNumbers: string[];
  normativeCardOccurrences: number;
  semanticTables: number;
  anomalyIds: string[];
}

export interface RuleDocument {
  path: string;
  part: RulePart;
  title: string;
  rawMarkdown: string;
  bodyMarkdown: string;
  sourcePages: SourcePage[];
}

export interface RuleChapter {
  part: "core" | "additional";
  number: number;
  numberPadded: string;
  title: string;
  titleMarkdown: string;
  route: string;
  markdown: string;
  sourcePages: number[];
  ruleHeadings: RuleHeading[];
  termIds: string[];
  cardNumbers: string[];
}

export interface AppendixPage {
  part: "appendix-1" | "appendix-2";
  number: 1 | 2;
  route: string;
  title: string;
  markdown: string;
  sourcePages: number[];
}

export interface SiteContent {
  source: {
    filename: string;
    version: string;
    pages: number;
    sha256: string;
  };
  documents: RuleDocument[];
  sourcePages: SourcePage[];
  chapters: {
    core: RuleChapter[];
    additional: RuleChapter[];
  };
  coreChapters: RuleChapter[];
  additionalChapters: RuleChapter[];
  appendices: AppendixPage[];
  glossary: GlossaryTerm[];
  glossaryById: ReadonlyMap<string, GlossaryTerm>;
  glossarySources: GlossarySource[];
  glossarySourceById: ReadonlyMap<string, GlossarySource>;
  metrics: {
    ruleHeadings: number;
    normativeCardOccurrences: number;
    semanticTables: number;
    revisions: Record<"2025-04-25-update" | "2025-06-02-tweak", number>;
    sourceAnomalies: number;
  };
}

interface TranslationManifest {
  source: SiteContent["source"];
  content_files: Array<{
    path: string;
    part: RulePart;
    pdf_pages: [number, number];
  }>;
  revision_segments: Record<string, Record<string, number>>;
  source_anomalies: Array<{ id: string; pdf_page: number; required_literals: string[] }>;
  official_graphic_replacement: {
    pdf_page: number;
    method: string;
    required_labels: string[];
  };
}

interface CoverageFile {
  metadata: {
    filename: string;
    version: string;
    pages: number;
    sha256: string;
  };
  pages: Array<{
    pdf_page: number;
    printed_page: number | null;
    part: string;
    rule_headings: Array<{ number: string; title: string }>;
    card_numbers: string[];
  }>;
}

const sourcePagePattern =
  /<!-- source-page: (\d+); printed-page: ([^;]+); part: ([^ ]+) -->\s*([\s\S]*?)<!-- \/source-page -->/g;
const termPattern = /\[\[([^\]|]+)\|([a-z0-9.-]+)\]\]/g;
const cardPattern = /NA-\d{2}(?:\/\d{2})?(?:-{1,2}[A-Za-z0-9/]+){2,}/g;
const transformCardPattern = /TransForm\s+Card\s+(?:A1-)?\d{2}/g;
const compactTransformCardPattern = /TransFormCard(?:A1-)?\d{2}/g;
const anomalyPattern = /<!-- source-anomaly: ([^; ]+)[^>]*-->/g;
const ruleHeadingPattern = /^(#{3,6})\s+(\d+(?:-\d+)+)\s+(.+)$/gm;
const normativeContentPaths = [
  "content/rules/zh-Hans/00-front-matter.md",
  "content/rules/zh-Hans/01-core-rules.md",
  "content/rules/zh-Hans/02-additional-rules.md",
  "content/rules/zh-Hans/03-appendix-goddess-list.md",
  "content/rules/zh-Hans/04-appendix-errata.md",
];

let cachedRoot = "";
let cachedContent: SiteContent | undefined;

function readJson<T>(root: string, relativePath: string): T {
  return JSON.parse(readFileSync(resolve(root, relativePath), "utf8")) as T;
}

function invariant(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new Error(`内容模型校验失败：${message}`);
  }
}

function unique<T>(values: Iterable<T>): T[] {
  return [...new Set(values)];
}

export function stripInlineMarkup(value: string): string {
  return value
    .replace(termPattern, "$1")
    .replace(/<span[^>]*>([\s\S]*?)<\/span>/g, "$1")
    .replace(/<[^>]+>/g, "")
    .replace(/[*_`]/g, "")
    .trim();
}

export function ruleAnchor(number: string): string {
  return `rule-${number.replaceAll("-", "-")}`;
}

function parseRuleHeadings(markdown: string): RuleHeading[] {
  return [...markdown.matchAll(ruleHeadingPattern)].map((match) => ({
    level: match[1].length,
    number: match[2],
    title: stripInlineMarkup(match[3]),
    anchor: ruleAnchor(match[2]),
  }));
}

function collectTermIds(markdown: string): string[] {
  return unique([...markdown.matchAll(termPattern)].map((match) => match[2]));
}

function collectCardNumbers(markdown: string): string[] {
  return unique([
    ...(markdown.match(cardPattern) ?? []),
    ...(markdown.match(transformCardPattern) ?? []),
  ]);
}

function countNormativeCardOccurrences(markdown: string): number {
  const withoutComments = markdown.replace(/<!--[\s\S]*?-->/g, "");
  const compact = withoutComments.replace(/<[^>]+>/g, "").normalize("NFKC").replace(/\s+/g, "");
  return (
    (compact.match(cardPattern) ?? []).length +
    (compact.match(compactTransformCardPattern) ?? []).length
  );
}

function collectAnomalyIds(markdown: string): string[] {
  return unique([...markdown.matchAll(anomalyPattern)].map((match) => match[1]));
}

function parseFrontmatter(raw: string): {
  attributes: Record<string, string>;
  body: string;
} {
  const match = raw.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  invariant(match, "规范译文缺少完整 YAML frontmatter");
  const attributes = Object.fromEntries(
    match[1]
      .split("\n")
      .map((line) => line.match(/^([a-z_]+):\s*"?([^"\n]+)"?$/))
      .filter((entry): entry is RegExpMatchArray => Boolean(entry))
      .map((entry) => [entry[1], entry[2]]),
  );
  return { attributes, body: match[2] };
}

function documentTitle(body: string): string {
  const heading = body.match(/^#\s+(.+)$/m);
  invariant(heading, "规范译文缺少一级标题");
  return stripInlineMarkup(heading[1]);
}

function parseSourcePages(body: string, expectedPart: RulePart): SourcePage[] {
  return [...body.matchAll(sourcePagePattern)].map((match) => {
    const part = match[3] as RulePart;
    invariant(part === expectedPart, `页标记 part=${part} 与文件 part=${expectedPart} 不一致`);
    const printedLiteral = match[2].trim();
    const printedPage = printedLiteral === "null" ? null : Number(printedLiteral);
    invariant(
      printedPage === null || Number.isInteger(printedPage),
      `PDF 第 ${match[1]} 页的印刷页码无效`,
    );
    return {
      pdfPage: Number(match[1]),
      printedPage,
      part,
      markdown: match[4].trim(),
      ruleHeadings: parseRuleHeadings(match[4]),
      termIds: collectTermIds(match[4]),
      cardNumbers: collectCardNumbers(match[4]),
      normativeCardOccurrences: countNormativeCardOccurrences(match[4]),
      semanticTables: [...match[4].matchAll(/<!-- table: rows=\d+; columns=\d+; id=[a-z0-9-]+ -->/g)].length,
      anomalyIds: collectAnomalyIds(match[4]),
    };
  });
}

function pagesOverlappingChapter(
  body: string,
  start: number,
  end: number,
  pages: SourcePage[],
): number[] {
  const markers = [...body.matchAll(sourcePagePattern)].map((match, index) => ({
    start: match.index ?? 0,
    end: (match.index ?? 0) + match[0].length,
    pdfPage: pages[index].pdfPage,
  }));
  return markers
    .filter((marker) => marker.end > start && marker.start < end)
    .map((marker) => marker.pdfPage);
}

function parseChapters(document: RuleDocument): RuleChapter[] {
  invariant(
    document.part === "core" || document.part === "additional",
    `不能从 ${document.part} 文档解析规则章节`,
  );
  const matches = [...document.bodyMarkdown.matchAll(/^## §(\d+)\s+(.+)$/gm)];
  return matches.map((match, index) => {
    const start = match.index ?? 0;
    const end = matches[index + 1]?.index ?? document.bodyMarkdown.length;
    const markdown = document.bodyMarkdown.slice(start, end).trim();
    const number = Number(match[1]);
    const numberPadded = String(number).padStart(2, "0");
    return {
      part: document.part as "core" | "additional",
      number,
      numberPadded,
      title: stripInlineMarkup(match[2]),
      titleMarkdown: match[2],
      route: `/rules/${document.part}/${numberPadded}/`,
      markdown,
      sourcePages: pagesOverlappingChapter(
        document.bodyMarkdown,
        start,
        end,
        document.sourcePages,
      ),
      ruleHeadings: parseRuleHeadings(markdown),
      termIds: collectTermIds(markdown),
      cardNumbers: collectCardNumbers(markdown),
    };
  });
}

function validateTerms(
  terms: GlossaryTerm[],
  documents: RuleDocument[],
): ReadonlyMap<string, GlossaryTerm> {
  invariant(terms.length === 171, `术语条目应为 171，实际为 ${terms.length}`);
  for (const term of terms) {
    invariant(/^[a-z0-9.-]+$/.test(term.id), `术语 ID 不合法：${term.id}`);
    invariant(Boolean(term.category), `${term.id} 缺少类别`);
    invariant(Boolean(term.recommended_zh), `${term.id} 缺少推荐简中`);
    invariant(Boolean(term.ja), `${term.id} 缺少日文原词`);
    invariant(Array.isArray(term.aliases), `${term.id} 别名不是数组`);
    invariant(new Set(term.aliases).size === term.aliases.length, `${term.id} 别名存在重复`);
    invariant(!term.aliases.includes(term.recommended_zh), `${term.id} 推荐名与别名重复`);
    invariant(Boolean(term.strict_definition), `${term.id} 缺少严格定义`);
    invariant(Boolean(term.plain_explanation), `${term.id} 缺少白话说明`);
    invariant(Array.isArray(term.anchors) && term.anchors.length > 0, `${term.id} 缺少规则锚点`);
    invariant(Array.isArray(term.evidence) && term.evidence.length > 0, `${term.id} 缺少来源证据`);
    invariant(["high", "medium", "low"].includes(term.confidence), `${term.id} 置信度无效`);
    invariant(["high", "medium", "low"].includes(term.impact), `${term.id} 影响等级无效`);
  }
  const byId = new Map(terms.map((term) => [term.id, term]));
  invariant(byId.size === terms.length, "术语 ID 存在重复");
  invariant(terms.every((term) => term.review_status === "locked"), "存在未锁定术语");

  for (const document of documents) {
    for (const match of document.bodyMarkdown.matchAll(termPattern)) {
      const term = byId.get(match[2]);
      invariant(term, `${document.path} 引用了未知术语 ${match[2]}`);
      invariant(
        match[1] === term.recommended_zh,
        `${document.path} 的 ${match[2]} 显示为“${match[1]}”，而锁定推荐名为“${term.recommended_zh}”`,
      );
    }
  }
  return byId;
}

function validateGlossarySources(
  sources: GlossarySource[],
  terms: GlossaryTerm[],
): ReadonlyMap<string, GlossarySource> {
  invariant(sources.length === 8, `术语证据来源应为 8，实际为 ${sources.length}`);
  const byId = new Map(sources.map((source) => [source.id, source]));
  invariant(byId.size === sources.length, "术语证据来源 ID 存在重复");
  for (const source of sources) {
    invariant(Boolean(source.id), "术语证据来源缺少 ID");
    invariant(Boolean(source.title), `${source.id} 缺少来源标题`);
    invariant(source.url.startsWith("https://"), `${source.id} 不是 HTTPS 来源`);
    invariant(/^\d{4}-\d{2}-\d{2}$/.test(source.accessed_at), `${source.id} 访问日期无效`);
    invariant(Boolean(source.evidence_summary), `${source.id} 缺少证据摘要`);
    invariant(Boolean(source.limitations), `${source.id} 缺少适用限制`);
  }
  for (const term of terms) {
    for (const evidence of term.evidence) {
      invariant(byId.has(evidence.source_id), `${term.id} 引用未知来源 ${evidence.source_id}`);
      invariant(Boolean(evidence.role), `${term.id} 的 ${evidence.source_id} 缺少证据角色`);
    }
  }
  return byId;
}

function validateCoverage(
  manifest: TranslationManifest,
  coverage: CoverageFile,
  pages: SourcePage[],
): void {
  invariant(manifest.source.pages === 86, `清单页数应为 86，实际为 ${manifest.source.pages}`);
  invariant(manifest.source.version === "1.14.1", "清单底本版本不为 1.14.1");
  invariant(manifest.source.sha256 === SOURCE_PDF_SHA256, "清单底本 SHA-256 不符合冻结值");
  invariant(coverage.metadata.pages === 86, "覆盖清单页数不为 86");
  invariant(coverage.metadata.filename === manifest.source.filename, "覆盖清单底本文件名不一致");
  invariant(coverage.metadata.version === manifest.source.version, "覆盖清单底本版本不一致");
  invariant(coverage.metadata.sha256 === SOURCE_PDF_SHA256, "覆盖清单底本 SHA-256 不符合冻结值");
  invariant(pages.length === 86, `译文页块应为 86，实际为 ${pages.length}`);
  invariant(coverage.pages.length === 86, "PDF 覆盖对象不为 86 页");
  invariant(
    pages.every((page, index) => page.pdfPage === index + 1),
    "译文 source-page 未按 1–86 连续排列",
  );
  for (const page of pages) {
    const source = coverage.pages[page.pdfPage - 1];
    invariant(source.pdf_page === page.pdfPage, `PDF 第 ${page.pdfPage} 页覆盖对象错位`);
    invariant(
      source.printed_page === page.printedPage,
      `PDF 第 ${page.pdfPage} 页印刷页码不一致`,
    );
    invariant(source.part === page.part, `PDF 第 ${page.pdfPage} 页 part 不一致`);
    invariant(
      source.rule_headings.map((heading) => heading.number).sort().join("|") ===
        page.ruleHeadings.map((heading) => heading.number).sort().join("|"),
      `PDF 第 ${page.pdfPage} 页规则标题编号与覆盖清单不一致`,
    );
    invariant(
      [...source.card_numbers].sort().join("|") === [...page.cardNumbers].sort().join("|"),
      `PDF 第 ${page.pdfPage} 页卡号与覆盖清单不一致`,
    );
  }
}

function validateRevisions(manifest: TranslationManifest, pages: SourcePage[]): void {
  const knownRevisions = new Set(Object.keys(manifest.revision_segments));
  for (const [revision, pageCounts] of Object.entries(manifest.revision_segments)) {
    for (const page of pages) {
      const expected = pageCounts[String(page.pdfPage)] ?? 0;
      const actual = [...page.markdown.matchAll(new RegExp(`data-revision="${revision}"`, "g"))]
        .length;
      invariant(
        actual === expected,
        `PDF 第 ${page.pdfPage} 页的 ${revision} 修订段应为 ${expected}，实际为 ${actual}`,
      );
    }
  }
  for (const page of pages) {
    for (const match of page.markdown.matchAll(/data-revision="([^"]+)"/g)) {
      invariant(knownRevisions.has(match[1]), `PDF 第 ${page.pdfPage} 页含未知修订类别 ${match[1]}`);
    }
  }
}

function validateSpecialMarkers(
  manifest: TranslationManifest,
  pages: SourcePage[],
): void {
  const actualAnomalies = pages.flatMap((page) => page.anomalyIds);
  const expectedAnomalies = manifest.source_anomalies.map((anomaly) => anomaly.id);
  invariant(
    [...actualAnomalies].sort().join("|") === [...expectedAnomalies].sort().join("|"),
    "源文异常标记与翻译清单不一致",
  );
  invariant(unique(actualAnomalies).length === actualAnomalies.length, "源文异常标记 ID 重复");
  for (const anomaly of manifest.source_anomalies) {
    const page = pages[anomaly.pdf_page - 1];
    invariant(page?.pdfPage === anomaly.pdf_page, `源文异常 ${anomaly.id} 页码超出覆盖范围`);
    invariant(page.anomalyIds.includes(anomaly.id), `源文异常 ${anomaly.id} 未出现在 PDF 第 ${anomaly.pdf_page} 页`);
    for (const literal of anomaly.required_literals) {
      invariant(page.markdown.includes(literal), `源文异常 ${anomaly.id} 缺少字面证据 ${literal}`);
    }
  }
  const graphicPage = pages[manifest.official_graphic_replacement.pdf_page - 1];
  invariant(
    graphicPage?.pdfPage === manifest.official_graphic_replacement.pdf_page,
    "机巧图示替换页超出覆盖范围",
  );
  const graphicMarkers =
    graphicPage.markdown.match(/original-graphic-replaced: contraption-icon-key/g) ?? [];
  invariant(graphicMarkers.length === 1, "第 45 页机巧图示替换标记应且只能出现一次");
  for (const label of manifest.official_graphic_replacement.required_labels) {
    invariant(graphicPage.markdown.includes(`- ${label}（`), `机巧图示替换缺少文字标签“${label}”`);
  }
}

export function loadSiteContent(projectRoot = process.cwd()): SiteContent {
  const root = resolve(projectRoot);
  if (cachedContent && cachedRoot === root) return cachedContent;

  const manifest = readJson<TranslationManifest>(root, "data/rules/translation-manifest.json");
  const coverage = readJson<CoverageFile>(root, "data/source/pdf-coverage.json");
  const glossaryFile = readJson<{ source_pdf_sha256: string; terms: GlossaryTerm[] }>(
    root,
    "data/glossary/terms.json",
  );
  const glossarySourcesFile = readJson<{ sources: GlossarySource[] }>(
    root,
    "data/glossary/sources.json",
  );
  invariant(glossaryFile.source_pdf_sha256 === SOURCE_PDF_SHA256, "术语源底本 SHA-256 不符合冻结值");
  invariant(manifest.content_files.length === 5, "翻译清单必须且只能列出五个规范译文文件");
  invariant(
    manifest.content_files.map((entry) => entry.path).join("|") === normativeContentPaths.join("|"),
    "翻译清单未按冻结顺序列出五个规范译文文件",
  );

  const documents = manifest.content_files.map((entry) => {
    const rawMarkdown = readFileSync(resolve(root, entry.path), "utf8");
    const { attributes, body } = parseFrontmatter(rawMarkdown);
    invariant(attributes.content_kind === "normative-rule", `${entry.path} content_kind 不正确`);
    invariant(attributes.language === "zh-Hans", `${entry.path} language 不正确`);
    invariant(attributes.source_version === "1.14.1", `${entry.path} source_version 不正确`);
    invariant(attributes.part === entry.part, `${entry.path} frontmatter part 不正确`);
    const sourcePages = parseSourcePages(body, entry.part);
    invariant(sourcePages.at(0)?.pdfPage === entry.pdf_pages[0], `${entry.path} 起始页不正确`);
    invariant(sourcePages.at(-1)?.pdfPage === entry.pdf_pages[1], `${entry.path} 结束页不正确`);
    return {
      path: entry.path,
      part: entry.part,
      title: documentTitle(body),
      rawMarkdown,
      bodyMarkdown: body,
      sourcePages,
    } satisfies RuleDocument;
  });

  const sourcePages = documents.flatMap((document) => document.sourcePages);
  validateCoverage(manifest, coverage, sourcePages);
  validateRevisions(manifest, sourcePages);
  validateSpecialMarkers(manifest, sourcePages);
  const glossarySourceById = validateGlossarySources(glossarySourcesFile.sources, glossaryFile.terms);
  const glossaryById = validateTerms(glossaryFile.terms, documents);

  const coreDocument = documents.find((document) => document.part === "core");
  const additionalDocument = documents.find((document) => document.part === "additional");
  invariant(coreDocument && additionalDocument, "缺少核心规则或追加规则文档");
  const coreChapters = parseChapters(coreDocument);
  const additionalChapters = parseChapters(additionalDocument);
  invariant(coreChapters.length === 10, `核心规则章节应为 10，实际为 ${coreChapters.length}`);
  invariant(
    additionalChapters.length === 24,
    `追加规则章节应为 24，实际为 ${additionalChapters.length}`,
  );
  invariant(
    coreChapters.every((chapter, index) => chapter.number === index + 1),
    "核心规则章节编号不连续",
  );
  invariant(
    additionalChapters.every((chapter, index) => chapter.number === index + 1),
    "追加规则章节编号不连续",
  );

  const appendices = (["appendix-1", "appendix-2"] as const).map((part, index) => {
    const document = documents.find((candidate) => candidate.part === part);
    invariant(document, `缺少 ${part} 文档`);
    const number = (index + 1) as 1 | 2;
    return {
      part,
      number,
      route: `/rules/appendix/0${number}/`,
      title: document.title,
      markdown: document.bodyMarkdown,
      sourcePages: document.sourcePages.map((page) => page.pdfPage),
    } satisfies AppendixPage;
  });

  cachedRoot = root;
  cachedContent = {
    source: manifest.source,
    documents,
    sourcePages,
    chapters: {
      core: coreChapters,
      additional: additionalChapters,
    },
    coreChapters,
    additionalChapters,
    appendices,
    glossary: glossaryFile.terms,
    glossaryById,
    glossarySources: glossarySourcesFile.sources,
    glossarySourceById,
    metrics: {
      ruleHeadings: sourcePages.reduce((sum, page) => sum + page.ruleHeadings.length, 0),
      normativeCardOccurrences: sourcePages.reduce(
        (sum, page) => sum + page.normativeCardOccurrences,
        0,
      ),
      semanticTables: sourcePages.reduce((sum, page) => sum + page.semanticTables, 0),
      revisions: {
        "2025-04-25-update": Object.values(manifest.revision_segments["2025-04-25-update"]).reduce(
          (sum, count) => sum + count,
          0,
        ),
        "2025-06-02-tweak": Object.values(manifest.revision_segments["2025-06-02-tweak"]).reduce(
          (sum, count) => sum + count,
          0,
        ),
      },
      sourceAnomalies: sourcePages.reduce((sum, page) => sum + page.anomalyIds.length, 0),
    },
  };
  return cachedContent;
}
