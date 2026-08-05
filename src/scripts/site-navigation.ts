class SiteNavigationElement extends HTMLElement {
  private toggle?: HTMLButtonElement;
  private closeButton?: HTMLButtonElement;
  private backdrop?: HTMLButtonElement;

  connectedCallback(): void {
    this.toggle = this.querySelector<HTMLButtonElement>(".nav-toggle") ?? undefined;
    this.closeButton = this.querySelector<HTMLButtonElement>(".nav-close") ?? undefined;
    this.backdrop = this.querySelector<HTMLButtonElement>(".nav-backdrop") ?? undefined;
    if (!this.toggle || !this.closeButton || !this.backdrop) return;
    this.classList.add("enhanced");
    this.toggle.hidden = false;
    this.closeButton.hidden = false;
    this.backdrop.hidden = false;
    this.toggle.addEventListener("click", () => this.open());
    this.closeButton.addEventListener("click", () => this.close());
    this.backdrop.addEventListener("click", () => this.close());
    this.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => this.close(false)));
    document.addEventListener("keydown", this.onKeydown);
  }

  disconnectedCallback(): void {
    document.removeEventListener("keydown", this.onKeydown);
  }

  private onKeydown = (event: KeyboardEvent): void => {
    if (event.key === "Escape" && this.classList.contains("is-open")) {
      event.preventDefault();
      this.close();
    }
  };

  private open(): void {
    this.classList.add("is-open");
    this.toggle?.setAttribute("aria-expanded", "true");
    queueMicrotask(() => this.closeButton?.focus());
  }

  private close(restoreFocus = true): void {
    const wasOpen = this.classList.contains("is-open");
    this.classList.remove("is-open");
    this.toggle?.setAttribute("aria-expanded", "false");
    if (wasOpen && restoreFocus) this.toggle?.focus();
  }
}
if (!customElements.get("site-navigation")) {
  customElements.define("site-navigation", SiteNavigationElement);
}
