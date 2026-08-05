import { describe, expect, it } from "vitest";

import {
  TERM_WORKSPACE_STORAGE_KEY,
  clampWindowRect,
  loadWorkspaceState,
  saveWorkspaceState,
  type WorkspaceState,
} from "../../src/lib/term-workspace-state";

class MemoryStorage implements Pick<Storage, "getItem" | "setItem"> {
  private values = new Map<string, string>();
  getItem(key: string): string | null {
    return this.values.get(key) ?? null;
  }
  setItem(key: string, value: string): void {
    this.values.set(key, value);
  }
}

describe("术语浮窗状态", () => {
  it("把位置与尺寸限制在视口安全区内", () => {
    expect(
      clampWindowRect(
        { x: -120, y: 900, width: 800, height: 900 },
        { width: 320, height: 568 },
      ),
    ).toEqual({ x: 8, y: 8, width: 304, height: 552 });
  });

  it("跨规则页面恢复至少三个固定术语及窗口属性", () => {
    const storage = new MemoryStorage();
    const state: WorkspaceState = {
      version: 1,
      windows: ["card.card", "zone.aura", "attack.damage"].map((termId, index) => ({
        termId,
        x: 24 + index * 32,
        y: 80 + index * 28,
        width: 340,
        height: 280,
        minimized: index === 1,
        z: index + 1,
      })),
    };
    saveWorkspaceState(storage, state);
    expect(storage.getItem(TERM_WORKSPACE_STORAGE_KEY)).not.toBeNull();
    expect(loadWorkspaceState(storage)).toEqual(state);
  });

  it("损坏的 sessionStorage 内容安全回退为空状态", () => {
    const storage = new MemoryStorage();
    storage.setItem(TERM_WORKSPACE_STORAGE_KEY, "not-json");
    expect(loadWorkspaceState(storage)).toEqual({ version: 1, windows: [] });
  });
});
