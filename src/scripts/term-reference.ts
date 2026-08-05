interface TermEventDetail {
  termId: string;
  source: HTMLElement;
}
class TermReferenceElement extends HTMLElement {
  private anchor?: HTMLAnchorElement;

  connectedCallback(): void {
    this.anchor = this.querySelector("a") ?? undefined;
    if (!this.anchor) return;
    this.anchor.addEventListener("mouseenter", this.preview);
    this.anchor.addEventListener("focus", this.preview);
    this.anchor.addEventListener("mouseleave", this.hidePreview);
    this.anchor.addEventListener("blur", this.hidePreview);
    this.anchor.addEventListener("click", this.pin);
    this.anchor.addEventListener("keydown", this.onKeydown);
  }

  private detail(): TermEventDetail {
    return { termId: this.dataset.termId ?? "", source: this };
  }

  private preview = (): void => {
    this.dispatchEvent(
      new CustomEvent<TermEventDetail>("furuyoni:term-preview", {
        bubbles: true,
        composed: true,
        detail: this.detail(),
      }),
    );
  };

  private hidePreview = (): void => {
    this.dispatchEvent(
      new CustomEvent<TermEventDetail>("furuyoni:term-preview-hide", {
        bubbles: true,
        composed: true,
        detail: this.detail(),
      }),
    );
  };

  private pin = (event: MouseEvent): void => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const workspace = document.querySelector("term-workspace.is-ready");
    if (!workspace) return;
    event.preventDefault();
    this.dispatchEvent(
      new CustomEvent<TermEventDetail>("furuyoni:term-pin", {
        bubbles: true,
        composed: true,
        detail: this.detail(),
      }),
    );
  };

  private onKeydown = (event: KeyboardEvent): void => {
    if (event.key !== " ") return;
    const workspace = document.querySelector("term-workspace.is-ready");
    if (!workspace) return;
    event.preventDefault();
    this.dispatchEvent(
      new CustomEvent<TermEventDetail>("furuyoni:term-pin", {
        bubbles: true,
        composed: true,
        detail: this.detail(),
      }),
    );
  };
}

if (!customElements.get("term-reference")) {
  customElements.define("term-reference", TermReferenceElement);
}
