export const TERM_WORKSPACE_STORAGE_KEY = "furuyoni-term-workspace-v1";

export interface WindowRect {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface ViewportSize {
  width: number;
  height: number;
}

export interface TermWindowState extends WindowRect {
  termId: string;
  minimized: boolean;
  z: number;
}

export interface WorkspaceState {
  version: 1;
  windows: TermWindowState[];
}

type StorageReader = Pick<Storage, "getItem">;
type StorageWriter = Pick<Storage, "setItem">;

const emptyState = (): WorkspaceState => ({ version: 1, windows: [] });

function finite(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isTermWindow(value: unknown): value is TermWindowState {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<TermWindowState>;
  return (
    typeof candidate.termId === "string" &&
    candidate.termId.length > 0 &&
    finite(candidate.x) &&
    finite(candidate.y) &&
    finite(candidate.width) &&
    finite(candidate.height) &&
    typeof candidate.minimized === "boolean" &&
    finite(candidate.z)
  );
}

export function clampWindowRect(
  rect: WindowRect,
  viewport: ViewportSize,
  margin = 8,
): WindowRect {
  const maximumWidth = Math.max(0, viewport.width - margin * 2);
  const maximumHeight = Math.max(0, viewport.height - margin * 2);
  const width = Math.min(Math.max(rect.width, Math.min(280, maximumWidth)), maximumWidth);
  const height = Math.min(Math.max(rect.height, Math.min(160, maximumHeight)), maximumHeight);
  const x = Math.min(Math.max(rect.x, margin), Math.max(margin, viewport.width - width - margin));
  const y = Math.min(Math.max(rect.y, margin), Math.max(margin, viewport.height - height - margin));
  return { x, y, width, height };
}

export function loadWorkspaceState(storage: StorageReader): WorkspaceState {
  try {
    const raw = storage.getItem(TERM_WORKSPACE_STORAGE_KEY);
    if (!raw) return emptyState();
    const parsed = JSON.parse(raw) as Partial<WorkspaceState>;
    if (parsed.version !== 1 || !Array.isArray(parsed.windows)) return emptyState();
    if (!parsed.windows.every(isTermWindow)) return emptyState();
    const seen = new Set<string>();
    return {
      version: 1,
      windows: parsed.windows.filter((windowState) => {
        if (seen.has(windowState.termId)) return false;
        seen.add(windowState.termId);
        return true;
      }),
    };
  } catch {
    return emptyState();
  }
}

export function saveWorkspaceState(storage: StorageWriter, state: WorkspaceState): void {
  try {
    storage.setItem(TERM_WORKSPACE_STORAGE_KEY, JSON.stringify(state));
  } catch {
    // sessionStorage 被禁用或容量不足时，交互仍可在当前页面继续使用。
  }
}
