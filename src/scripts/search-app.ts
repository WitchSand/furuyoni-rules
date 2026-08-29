import { glossaryTermMatchesQuery } from "../lib/search-normalization";
import type { GlossaryTerm } from "../lib/content-model";

interface PagefindResultData {
  url: string;
  excerpt: string;
  meta: { title?: string };
  filters?: Record<string, string | string[]>;
}

interface GlossaryPayload {
  terms: GlossaryTerm[];
  routes: Record<string, string>;
}

interface PagefindSearchResult {
  id: string;
  data: () => Promise<PagefindResultData>;
}

interface PagefindModule {
  init: () => Promise<void>;
  options?: (options: { baseUrl: string }) => Promise<void>;
  search: (
    query: string,
    options?: { filters?: Record<string, string> },
  ) => Promise<{ results: PagefindSearchResult[] }>;
}

class SearchAppElement extends HTMLElement {
  private pagefind?: PagefindModule;
  private form?: HTMLFormElement;
  private input?: HTMLInputElement;
  private status?: HTMLElement;
  private results?: HTMLOListElement;
  private selects: HTMLSelectElement[] = [];
  private glossary?: GlossaryPayload;

  connectedCallback(): void {
    this.form = this.querySelector("form") ?? undefined;
    this.input = this.querySelector("input[type=search]") ?? undefined;
    this.status = this.querySelector(".search-status") ?? undefined;
    this.results = this.querySelector(".search-results") ?? undefined;
    this.selects = [...this.querySelectorAll<HTMLSelectElement>("select[data-filter]")];
    if (!this.form || !this.input || !this.status || !this.results) return;
    this.form.addEventListener("submit", (event) => {
      event.preventDefault();
      void this.runSearch();
    });
    this.selects.forEach((select) => select.addEventListener("change", () => void this.runSearch()));
    this.restoreQuery();
    void this.initialize();
  }

  private async initialize(): Promise<void> {
    this.setStatus("正在载入离线搜索索引……");
    try {
      const base = this.dataset.base || "/";
      this.pagefind = (await import(/* @vite-ignore */ `${base}pagefind/pagefind.js`)) as PagefindModule;
      await this.pagefind.init();
      await this.pagefind.options?.({ baseUrl: base });
      const glossaryResponse = await fetch(`${base}data/glossary.json`);
      if (!glossaryResponse.ok) throw new Error(`术语数据载入失败：${glossaryResponse.status}`);
      this.glossary = (await glossaryResponse.json()) as GlossaryPayload;
      this.classList.add("is-ready");
      if (this.input?.value.trim()) await this.runSearch(false);
      else this.setStatus("输入推荐简中、日文、社区别名、女神名、规则编号或卡号。", false);
    } catch (error) {
      this.setStatus("搜索索引载入失败。规则正文与术语页仍可通过章节导航访问。", false);
      console.error(error);
    }
  }

  private restoreQuery(): void {
    const params = new URLSearchParams(location.search);
    if (this.input) this.input.value = params.get("q") ?? "";
    for (const select of this.selects) {
      select.value = params.get(select.dataset.filter ?? "") ?? "";
    }
  }

  private async runSearch(updateUrl = true): Promise<void> {
    const query = this.input?.value.trim() ?? "";
    if (!this.pagefind) return;
    if (!query) {
      this.results?.replaceChildren();
      this.setStatus("请输入搜索内容。", false);
      return;
    }
    const filters = Object.fromEntries(
      this.selects
        .filter((select) => select.value)
        .map((select) => [select.dataset.filter ?? "", select.value]),
    );
    this.setStatus("正在搜索……");
    try {
      const response = await this.pagefind.search(query, {
        filters: Object.keys(filters).length ? filters : undefined,
      });
      const pagefindData = await Promise.all(response.results.map((result) => result.data()));
      const data = this.mergeGlossaryMatches(pagefindData, query, filters);
      this.renderResults(data);
      this.setStatus(`找到 ${data.length} 条结果。`, false);
      if (updateUrl) this.updateUrl(query, filters);
    } catch (error) {
      this.setStatus("搜索失败，请调整关键词后重试。", false);
      console.error(error);
    }
  }

  private mergeGlossaryMatches(
    pagefindData: PagefindResultData[],
    query: string,
    filters: Record<string, string>,
  ): PagefindResultData[] {
    if (!this.glossary || filters.kind === "规则" || filters.goddess) return pagefindData;
    const directMatches = this.glossary.terms
      .filter((term) => !filters.category || term.category === filters.category)
      .filter((term) => !filters.confidence || term.confidence === filters.confidence)
      .filter((term) => glossaryTermMatchesQuery(term, query))
      .map((term) => ({
        url: this.glossary!.routes[term.id],
        excerpt: `规范术语：${this.escapeHtml(term.recommended_zh)}；别名：${this.escapeHtml(term.aliases.join("、") || "无")}`,
        meta: { title: `${term.recommended_zh}｜术语` },
        filters: {
          kind: "术语",
          category: term.category,
          confidence: term.confidence,
        },
      }));
    const seen = new Set(directMatches.map((item) => item.url));
    return [...directMatches, ...pagefindData.filter((item) => !seen.has(item.url))];
  }

  private escapeHtml(value: string): string {
    return value.replace(/[&<>"']/g, (character) => {
      const entities: Record<string, string> = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      };
      return entities[character];
    });
  }

  private renderResults(items: PagefindResultData[]): void {
    if (!this.results) return;
    this.results.replaceChildren();
    for (const item of items) {
      const row = document.createElement("li");
      row.className = "search-result";
      const heading = document.createElement("h2");
      const link = document.createElement("a");
      link.href = item.url;
      link.textContent = item.meta.title || "未命名结果";
      heading.append(link);
      const excerpt = document.createElement("p");
      excerpt.innerHTML = item.excerpt;
      row.append(heading, excerpt);
      this.results.append(row);
    }
  }

  private updateUrl(query: string, filters: Record<string, string>): void {
    const params = new URLSearchParams({ q: query });
    for (const [key, value] of Object.entries(filters)) params.set(key, value);
    history.replaceState(null, "", `${location.pathname}?${params}`);
  }

  private setStatus(message: string, busy = true): void {
    if (!this.status) return;
    this.status.textContent = message;
    this.status.setAttribute("aria-busy", String(busy));
  }
}

if (!customElements.get("search-app")) {
  customElements.define("search-app", SearchAppElement);
}
