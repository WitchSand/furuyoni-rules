import type { GlossaryTerm, SiteContent } from "./content-model";

export function normalizeSearchText(value: string): string {
  return value
    .normalize("NFKC")
    .toLocaleLowerCase("zh-CN")
    .replace(/[‐‑‒–—―﹘﹣]/g, "-")
    .replace(/[“”‘’「」『』《》〈〉]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function buildGlossarySearchText(term: GlossaryTerm): string {
  return [
    term.recommended_zh,
    term.ja,
    ...term.aliases,
    term.strict_definition,
    term.plain_explanation,
    term.id,
  ]
    .filter(Boolean)
    .join(" · ");
}

export function glossaryTermMatchesQuery(term: GlossaryTerm, query: string): boolean {
  const normalizedQuery = normalizeSearchText(query);
  if (!normalizedQuery) return false;
  return [term.recommended_zh, term.ja, ...term.aliases, term.id]
    .map(normalizeSearchText)
    .some((value) => value.includes(normalizedQuery));
}

export function additionalChapterGoddess(
  chapterNumber: number,
  content: SiteContent,
): string | undefined {
  if (chapterNumber < 3 || chapterNumber > 24) return undefined;
  const goddessId = `goddess.${String(chapterNumber + 2).padStart(2, "0")}`;
  return content.glossaryById.get(goddessId)?.recommended_zh;
}

export function termGoddessFilters(term: GlossaryTerm, content: SiteContent): string[] {
  const filters = new Set<string>();
  if (term.category === "goddess" || term.id.startsWith("goddess.")) {
    filters.add(term.recommended_zh);
  }
  for (const anchor of term.anchors) {
    if (anchor.part !== "additional" || !anchor.rule) continue;
    const chapterNumber = Number(anchor.rule.split("-")[0]);
    const chapter = content.additionalChapters.find(
      (candidate) => candidate.number === chapterNumber,
    );
    const goddess = chapter ? additionalChapterGoddess(chapter.number, content) : undefined;
    if (goddess) filters.add(goddess);
  }
  return [...filters];
}
