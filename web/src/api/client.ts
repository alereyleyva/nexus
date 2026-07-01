import type { ProblemDetails, TokenResponse } from "@/api/types";
import { tokenStore } from "@/auth/tokenStore";

export const API_URL: string =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ??
  "http://localhost:8000";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly problem: ProblemDetails | null;

  constructor(status: number, problem: ProblemDetails | null, fallback: string) {
    super(problem?.detail ?? fallback);
    this.name = "ApiError";
    this.status = status;
    this.code = problem?.code ?? "UNKNOWN";
    this.problem = problem;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  /** Internal: prevents refresh recursion. */
  retryOnUnauthorized?: boolean;
}

function requestId(): string {
  try {
    return crypto.randomUUID();
  } catch {
    return `req-${Date.now()}-${Math.floor(Math.random() * 1e6)}`;
  }
}

async function parseProblem(response: Response): Promise<ProblemDetails | null> {
  try {
    return (await response.json()) as ProblemDetails;
  } catch {
    return null;
  }
}

let refreshInFlight: Promise<boolean> | null = null;

async function refreshSession(): Promise<boolean> {
  const refreshToken = tokenStore.getRefreshToken();
  if (!refreshToken) return false;
  refreshInFlight ??= (async () => {
    try {
      const response = await fetch(`${API_URL}/v1/auth/session/refresh`, {
        method: "POST",
        headers: { "content-type": "application/json", "X-Request-Id": requestId() },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!response.ok) {
        tokenStore.clear();
        return false;
      }
      const tokens = (await response.json()) as TokenResponse;
      tokenStore.setSession(tokens);
      return true;
    } catch {
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();
  return refreshInFlight;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, retryOnUnauthorized = true } = options;
  const headers: Record<string, string> = { "X-Request-Id": requestId() };
  const accessToken = tokenStore.getAccessToken();
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  if (body !== undefined) headers["content-type"] = "application/json";

  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401 && retryOnUnauthorized && (await refreshSession())) {
    return apiRequest<T>(path, { ...options, retryOnUnauthorized: false });
  }

  if (!response.ok) {
    const problem = await parseProblem(response);
    if (response.status === 401) tokenStore.clear();
    throw new ApiError(response.status, problem, response.statusText);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
