// Empty defaults = same-origin relative paths (single-port Docker/nginx serving; Vite dev proxies /api).
export const API_BASE: string = import.meta.env.VITE_API_BASE ?? "";
export const WS_BASE: string = import.meta.env.VITE_WS_BASE ?? "";
/** Origin for join/QR links; set to the LAN IP / public host so phones can reach it. */
export const PUBLIC_BASE: string =
  import.meta.env.VITE_PUBLIC_BASE || globalThis.location?.origin || "";

export class ApiError extends Error {
  status: number;
  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function request<T>(
  path: string,
  opts: { method?: string; body?: unknown; token?: string; query?: Record<string, string> } = {},
): Promise<T> {
  const qs = opts.query ? "?" + new URLSearchParams(opts.query).toString() : "";
  const headers: Record<string, string> = {};
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";
  if (opts.token) headers["Authorization"] = `Bearer ${opts.token}`;
  const res = await fetch(`${API_BASE}${path}${qs}`, {
    method: opts.method ?? (opts.body !== undefined ? "POST" : "GET"),
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) {
    let detail = "Erro inesperado. Tente novamente.";
    try {
      const j = await res.json();
      if (typeof j?.detail === "string") detail = j.detail;
    } catch {
      // non-JSON error body: keep the generic message
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204 || res.headers.get("content-length") === "0") return undefined as T;
  return (await res.json()) as T;
}

/** Builds a ws(s):// URL; uses VITE_WS_BASE if set, else derives from the page origin. */
export function wsUrl(path: string, query?: Record<string, string>): string {
  const base = WS_BASE || globalThis.location.origin.replace(/^http/, "ws");
  return `${base}${path}${query ? "?" + new URLSearchParams(query).toString() : ""}`;
}
