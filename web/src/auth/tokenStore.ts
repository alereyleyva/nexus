// Access token lives in memory; only the refresh token is persisted (browser
// storage), per standards/frontend/repository-structure.md.

import type { TokenResponse } from "@/api/types";

const REFRESH_KEY = "nexus.refresh_token";

let accessToken: string | null = null;
const listeners = new Set<() => void>();

function notify(): void {
  for (const listener of listeners) listener();
}

export const tokenStore = {
  getAccessToken(): string | null {
    return accessToken;
  },
  getRefreshToken(): string | null {
    try {
      return localStorage.getItem(REFRESH_KEY);
    } catch {
      return null;
    }
  },
  setSession(tokens: Pick<TokenResponse, "access_token" | "refresh_token">): void {
    accessToken = tokens.access_token;
    try {
      localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
    } catch {
      /* storage unavailable — session survives only in memory */
    }
    notify();
  },
  clear(): void {
    accessToken = null;
    try {
      localStorage.removeItem(REFRESH_KEY);
    } catch {
      /* ignore */
    }
    notify();
  },
  hasSession(): boolean {
    return accessToken !== null || tokenStore.getRefreshToken() !== null;
  },
  subscribe(listener: () => void): () => void {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
};
