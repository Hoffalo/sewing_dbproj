import { getCsrfToken } from "./csrf";

const BASE = "/api";

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, message: string, body: unknown) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

type Method = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

async function request<T>(
  path: string,
  method: Method = "GET",
  body?: unknown,
  opts: { params?: Record<string, string | number | undefined> } = {}
): Promise<T> {
  const url = new URL(BASE + path, window.location.origin);
  if (opts.params) {
    for (const [k, v] of Object.entries(opts.params)) {
      if (v !== undefined && v !== "") url.searchParams.set(k, String(v));
    }
  }

  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (method !== "GET") {
    const token = getCsrfToken();
    if (token) headers["X-CSRFToken"] = token;
  }

  const res = await fetch(url.toString(), {
    method,
    credentials: "include",
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 204) return undefined as T;

  let payload: unknown;
  const ct = res.headers.get("content-type") ?? "";
  if (ct.includes("application/json")) payload = await res.json();
  else payload = await res.text();

  if (!res.ok) {
    const detail =
      (payload && typeof payload === "object" && "detail" in payload
        ? (payload as { detail: string }).detail
        : null) ?? `HTTP ${res.status}`;
    throw new ApiError(res.status, detail, payload);
  }

  return payload as T;
}

export const api = {
  get: <T>(path: string, params?: Record<string, string | number | undefined>) =>
    request<T>(path, "GET", undefined, { params }),
  post: <T>(path: string, body?: unknown) => request<T>(path, "POST", body),
  put: <T>(path: string, body?: unknown) => request<T>(path, "PUT", body),
  patch: <T>(path: string, body?: unknown) => request<T>(path, "PATCH", body),
  delete: <T>(path: string) => request<T>(path, "DELETE"),
  primeCsrf: () => request<{ csrftoken: string }>("/auth/csrf/", "GET"),
};
