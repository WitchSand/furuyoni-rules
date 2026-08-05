import type { GlossaryTerm } from "../lib/content-model";
import {
  clampWindowRect,
  loadWorkspaceState,
  saveWorkspaceState,
  type TermWindowState,
  type WorkspaceState,
} from "../lib/term-workspace-state";
import { categoryLabels, confidenceLabels } from "../lib/routes";

interface GlossaryPayload {
  terms: GlossaryTerm[];
  routes: Record<string, string>;
}

interface TermEventDetail {
  termId: string;
  source: HTMLElement;
}

const mobileQuery = matchMedia("(max-width: 52rem)");

class TermWorkspaceElement extends HTMLElement {
  private terms = new Map<string, GlossaryTerm>();
  private routes: Record<string, string> = {};
  private states: TermWindowState[] = [];
  private layer?: HTMLElement;
  private preview?: HTMLElement;
  private mobileToggle?: HTMLButtonElement;
  private zCounter = 1;
  private resizeObservers = new Map<string, ResizeObserver>();

  connectedCallback(): void {
    this.layer = this.querySelector<HTMLElement>(".term-window-layer") ?? undefined;
    this.preview = this.querySelector<HTMLElement>(".term-preview") ?? undefined;
    this.mobileToggle = this.querySelector<HTMLButtonElement>(".term-mobile-toggle") ?? undefined;
    if (!this.layer || !this.preview || !this.mobileToggle) return;
    this.classList.add("enhanced");
    this.mobileToggle.hidden = false;
    this.mobileToggle.addEventListener("click", () => {
      const open = this.classList.toggle("mobile-open");
      this.mobileToggle?.setAttribute("aria-expanded", String(open));
      if (open) queueMicrotask(() => this.layer?.querySelector<HTMLButtonElement>("button")?.focus());
    });
    document.addEventListener("furuyoni:term-preview", this.onPreview as EventListener);
    document.addEventListener("furuyoni:term-preview-hide", this.onPreviewHide as EventListener);
    document.addEventListener("furuyoni:term-pin", this.onPin as EventListener);
    document.addEventListener("keydown", this.onKeydown);
    window.addEventListener("resize", this.onViewportChange);
    mobileQuery.addEventListener("change", this.onViewportChange);
    void this.load();
  }

  disconnectedCallback(): void {
    document.removeEventListener("furuyoni:term-preview", this.onPreview as EventListener);
    document.removeEventListener("furuyoni:term-preview-hide", this.onPreviewHide as EventListener);
    document.removeEventListener("furuyoni:term-pin", this.onPin as EventListener);
    document.removeEventListener("keydown", this.onKeydown);
    window.removeEventListener("resize", this.onViewportChange);
    mobileQuery.removeEventListener("change", this.onViewportChange);
    this.resizeObservers.forEach((observer) => observer.disconnect());
  }

  private async load(): Promise<void> {
    try {
      const response = await fetch(this.dataset.source ?? "", { credentials: "same-origin" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = (await response.json()) as GlossaryPayload;
      this.terms = new Map(payload.terms.map((term) => [term.id, term]));
      this.routes = payload.routes;
      const restored = loadWorkspaceState(sessionStorage).windows.filter((state) => this.terms.has(state.termId));
      this.states = mobileQuery.matches
        ? restored
        : restored.map((state) => ({
            ...state,
            ...clampWindowRect(state, { width: innerWidth, height: innerHeight }),
          }));
      this.zCounter = Math.max(1, ...this.states.map((state) => state.z + 1));
      this.classList.add("is-ready");
      this.renderAll();
    } catch (error) {
      console.warn("术语工作区载入失败，保留普通术语链接。", error);
    }
  }

  private onPreview = (event: CustomEvent<TermEventDetail>): void => {
    if (mobileQuery.matches || !this.preview || !this.classList.contains("is-ready")) return;
    const term = this.terms.get(event.detail.termId);
    if (!term || this.states.some((state) => state.termId === term.id)) return;
    this.preview.replaceChildren(this.termSummary(term, false));
    this.preview.hidden = false;
    const anchor = event.detail.source.getBoundingClientRect();
    const width = Math.min(352, window.innerWidth - 16);
    const estimatedHeight = Math.min(this.preview.scrollHeight || 240, window.innerHeight - 16);
    const x = Math.min(Math.max(8, anchor.left), window.innerWidth - width - 8);
    const yBelow = anchor.bottom + 8;
    const y = yBelow + estimatedHeight <= window.innerHeight
      ? yBelow
      : Math.max(8, anchor.top - estimatedHeight - 8);
    Object.assign(this.preview.style, { left: `${x}px`, top: `${y}px`, width: `${width}px` });
  };

  private onPreviewHide = (): void => {
    if (this.preview) this.preview.hidden = true;
  };

  private onPin = (event: CustomEvent<TermEventDetail>): void => {
    if (!this.terms.has(event.detail.termId)) return;
    this.pin(event.detail.termId);
  };

  private onKeydown = (event: KeyboardEvent): void => {
    if (event.key === "Escape" && this.classList.contains("mobile-open")) {
      this.classList.remove("mobile-open");
      this.mobileToggle?.setAttribute("aria-expanded", "false");
      this.mobileToggle?.focus();
    }
  };

  private onViewportChange = (): void => {
    if (!mobileQuery.matches) {
      this.states = this.states.map((state) => ({
        ...state,
        ...clampWindowRect(state, { width: innerWidth, height: innerHeight }),
      }));
      this.applyAllGeometry();
      this.persist();
    }
  };

  private pin(termId: string): void {
    const existing = this.states.find((state) => state.termId === termId);
    if (existing) {
      existing.z = this.zCounter++;
      this.renderAll();
      return;
    }
    const offset = this.states.length % 6;
    const rect = clampWindowRect(
      { x: 32 + offset * 34, y: 96 + offset * 30, width: 352, height: 288 },
      { width: innerWidth, height: innerHeight },
    );
    this.states.push({ termId, ...rect, minimized: false, z: this.zCounter++ });
    this.renderAll();
    if (mobileQuery.matches) {
      this.classList.add("mobile-open");
      this.mobileToggle?.setAttribute("aria-expanded", "true");
    }
  }

  private renderAll(): void {
    if (!this.layer) return;
    this.resizeObservers.forEach((observer) => observer.disconnect());
    this.resizeObservers.clear();
    this.layer.replaceChildren();
    for (const state of [...this.states].sort((left, right) => left.z - right.z)) {
      const term = this.terms.get(state.termId);
      if (!term) continue;
      this.layer.append(this.termWindow(term, state));
    }
    this.classList.toggle("has-pins", this.states.length > 0);
    const count = this.querySelector<HTMLElement>(".term-count");
    if (count) count.textContent = String(this.states.length);
    if (this.states.length === 0) {
      this.classList.remove("mobile-open");
      this.mobileToggle?.setAttribute("aria-expanded", "false");
    }
    this.persist();
  }

  private termWindow(term: GlossaryTerm, state: TermWindowState): HTMLElement {
    const article = document.createElement("article");
    article.className = `term-window${state.minimized ? " is-minimized" : ""}`;
    article.dataset.termId = term.id;
    article.setAttribute("role", "dialog");
    article.setAttribute("aria-label", `固定术语：${term.recommended_zh}`);
    Object.assign(article.style, {
      left: `${state.x}px`,
      top: `${state.y}px`,
      width: `${state.width}px`,
      height: `${state.height}px`,
      zIndex: String(state.z),
    });

    const header = document.createElement("header");
    header.className = "term-window-header";
    header.tabIndex = 0;
    header.setAttribute("role", "group");
    header.setAttribute("aria-label", "术语窗移动区；方向键移动，Shift 加方向键调整大小");
    const title = document.createElement("h2");
    title.textContent = term.recommended_zh;
    const minimize = this.iconButton(state.minimized ? "还原" : "最小化", state.minimized ? "□" : "—");
    const front = this.iconButton("置顶", "↑");
    const close = this.iconButton("关闭", "×");
    header.append(title, minimize, front, close);
    const body = document.createElement("div");
    body.className = "term-window-body";
    body.append(this.termSummary(term, true));
    article.append(header, body);

    minimize.addEventListener("click", () => {
      state.minimized = !state.minimized;
      state.z = this.zCounter++;
      this.renderAll();
    });
    front.addEventListener("click", () => {
      state.z = this.zCounter++;
      this.renderAll();
    });
    close.addEventListener("click", () => {
      this.states = this.states.filter((candidate) => candidate.termId !== state.termId);
      this.renderAll();
    });
    article.addEventListener("pointerdown", () => {
      if (state.z < this.zCounter - 1) {
        state.z = this.zCounter++;
        article.style.zIndex = String(state.z);
        this.persist();
      }
    });
    this.enableKeyboardGeometry(header, article, state);
    this.enableDrag(header, article, state);
    const observer = new ResizeObserver(() => {
      if (mobileQuery.matches || state.minimized) return;
      const rect = article.getBoundingClientRect();
      const clamped = clampWindowRect(
        { x: rect.left, y: rect.top, width: rect.width, height: rect.height },
        { width: innerWidth, height: innerHeight },
      );
      Object.assign(state, clamped);
      Object.assign(article.style, {
        left: `${clamped.x}px`,
        top: `${clamped.y}px`,
        width: `${clamped.width}px`,
        height: `${clamped.height}px`,
      });
      this.persist();
    });
    observer.observe(article);
    this.resizeObservers.set(state.termId, observer);
    return article;
  }

  private iconButton(label: string, symbol: string): HTMLButtonElement {
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("aria-label", label);
    button.title = label;
    button.textContent = symbol;
    return button;
  }

  private termSummary(term: GlossaryTerm, withActions: boolean): DocumentFragment {
    const fragment = document.createDocumentFragment();
    const ja = document.createElement("p");
    ja.lang = "ja";
    ja.textContent = term.ja || "（无独立日文原词）";
    const definition = document.createElement("p");
    definition.textContent = term.strict_definition;
    const plain = document.createElement("p");
    plain.textContent = term.plain_explanation;
    const meta = document.createElement("small");
    meta.textContent = `${categoryLabels[term.category] ?? term.category} · 置信度 ${confidenceLabels[term.confidence] ?? term.confidence} · 已锁定`;
    fragment.append(ja, definition, plain, meta);
    if (term.aliases.length > 0) {
      const aliases = document.createElement("p");
      aliases.className = "search-aliases";
      aliases.textContent = `社区别名（仅检索）：${term.aliases.join("、")}`;
      fragment.append(aliases);
    }
    if (withActions) {
      const actions = document.createElement("div");
      actions.className = "term-window-actions";
      const link = document.createElement("a");
      link.href = this.routes[term.id] ?? `../glossary/${term.id}/`;
      link.textContent = "打开独立术语页";
      actions.append(link);
      fragment.append(actions);
    }
    return fragment;
  }

  private enableDrag(header: HTMLElement, article: HTMLElement, state: TermWindowState): void {
    header.addEventListener("pointerdown", (event) => {
      if (mobileQuery.matches || (event.target as HTMLElement).closest("button")) return;
      event.preventDefault();
      header.setPointerCapture(event.pointerId);
      state.z = this.zCounter++;
      article.style.zIndex = String(state.z);
      const startX = event.clientX;
      const startY = event.clientY;
      const originX = state.x;
      const originY = state.y;
      const move = (moveEvent: PointerEvent): void => {
        const clamped = clampWindowRect(
          {
            x: originX + moveEvent.clientX - startX,
            y: originY + moveEvent.clientY - startY,
            width: state.width,
            height: state.height,
          },
          { width: innerWidth, height: innerHeight },
        );
        Object.assign(state, clamped);
        article.style.left = `${state.x}px`;
        article.style.top = `${state.y}px`;
      };
      const finish = (): void => {
        header.removeEventListener("pointermove", move);
        header.removeEventListener("pointerup", finish);
        header.removeEventListener("pointercancel", finish);
        this.persist();
      };
      header.addEventListener("pointermove", move);
      header.addEventListener("pointerup", finish);
      header.addEventListener("pointercancel", finish);
    });
  }

  private enableKeyboardGeometry(
    header: HTMLElement,
    article: HTMLElement,
    state: TermWindowState,
  ): void {
    header.addEventListener("keydown", (event) => {
      if (
        mobileQuery.matches
        || event.target !== header
        || !["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)
      ) {
        return;
      }
      event.preventDefault();
      const step = event.altKey ? 1 : 16;
      const horizontal = event.key === "ArrowLeft" ? -step : event.key === "ArrowRight" ? step : 0;
      const vertical = event.key === "ArrowUp" ? -step : event.key === "ArrowDown" ? step : 0;
      const next = event.shiftKey
        ? { ...state, width: state.width + horizontal, height: state.height + vertical }
        : { ...state, x: state.x + horizontal, y: state.y + vertical };
      Object.assign(
        state,
        clampWindowRect(next, { width: innerWidth, height: innerHeight }),
        { z: this.zCounter++ },
      );
      Object.assign(article.style, {
        left: `${state.x}px`,
        top: `${state.y}px`,
        width: `${state.width}px`,
        height: `${state.height}px`,
        zIndex: String(state.z),
      });
      this.persist();
    });
  }

  private applyAllGeometry(): void {
    for (const state of this.states) {
      const windowElement = this.layer?.querySelector<HTMLElement>(`[data-term-id="${CSS.escape(state.termId)}"]`);
      if (!windowElement) continue;
      Object.assign(windowElement.style, {
        left: `${state.x}px`,
        top: `${state.y}px`,
        width: `${state.width}px`,
        height: `${state.height}px`,
      });
    }
  }

  private persist(): void {
    const state: WorkspaceState = { version: 1, windows: this.states };
    saveWorkspaceState(sessionStorage, state);
  }
}

if (!customElements.get("term-workspace")) {
  customElements.define("term-workspace", TermWorkspaceElement);
}
