interface PagefindResultData {
  url: string;
  excerpt: string;
  meta: { title?: string };
  filters?: Record<string, string | string[]>;
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
      const data = await Promise.all(response.results.map((result) => result.data()));
      this.renderResults(data);
      this.setStatus(`找到 ${data.length} 条结果。`, false);
      if (updateUrl) this.updateUrl(query, filters);
    } catch (error) {
      this.setStatus("搜索失败，请调整关键词后重试。", false);
      console.error(error);
    }
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
