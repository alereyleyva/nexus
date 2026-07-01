import { apiRequest } from "@/api/client";
import type { ActorContext, TokenResponse } from "@/api/types";

export function devLogin(email: string): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/v1/auth/web/dev-login", {
    method: "POST",
    body: { email },
    retryOnUnauthorized: false,
  });
}

export function fetchMe(): Promise<ActorContext> {
  return apiRequest<ActorContext>("/v1/auth/me");
}

export function revokeSession(): Promise<void> {
  return apiRequest<void>("/v1/auth/session/revoke", { method: "POST", body: {} });
}
