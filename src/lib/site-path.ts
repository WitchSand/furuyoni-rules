export function normalizeBase(base: string): string {
  const normalized = `/${base}`.replace(/\/{2,}/g, "/");
  return normalized === "/" ? "/" : `/${normalized.replace(/^\/+|\/+$/g, "")}/`;
}

export function sitePath(path: string, base = "/"): string {
  if (/^(?:https?:|mailto:|tel:)/.test(path)) return path;
  const normalizedBase = normalizeBase(base);
  const suffixIndex = path.search(/[?#]/u);
  const pathname = suffixIndex === -1 ? path : path.slice(0, suffixIndex);
  const suffix = suffixIndex === -1 ? "" : path.slice(suffixIndex);
  const cleanPath = pathname.replace(/^\/+/, "");
  return `${normalizedBase}${cleanPath}`.replace(/\/{2,}/g, "/") + suffix;
}
