import { API_URL, apiRequest } from "@/api/client";
import type {
  ActorContext,
  AuthProvider,
  CliAuthorizationDecision,
  CliAuthorizationView,
  TokenResponse,
} from "@/api/types";

export function fetchProviders(): Promise<{ providers: AuthProvider[] }> {
  return apiRequest<{ providers: AuthProvider[] }>("/v1/auth/providers", {
    retryOnUnauthorized: false,
  });
}

export function devLogin(email: string): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/v1/auth/web/dev-login", {
    method: "POST",
    body: { email },
    retryOnUnauthorized: false,
  });
}

/** Web origin the API redirects back to after Google OIDC. */
export function webOrigin(): string {
  return window.location.origin;
}

/** Full-page destination that kicks off the Google OIDC redirect flow. */
export function oidcAuthorizeUrl(): string {
  const redirectUri = `${webOrigin()}/auth/callback`;
  return `${API_URL}/v1/auth/oidc/google/authorize?redirect_uri=${encodeURIComponent(redirectUri)}`;
}

/** Exchange a one-time OIDC login_code for a standard Nexus session. */
export function exchangeWebSession(loginCode: string): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/v1/auth/web/session", {
    method: "POST",
    body: { login_code: loginCode },
    retryOnUnauthorized: false,
  });
}

/** Public read of a pending CLI device-login request for the verification page. */
export function getCliAuthorization(userCode: string): Promise<CliAuthorizationView> {
  return apiRequest<CliAuthorizationView>(
    `/v1/auth/cli/authorizations/${encodeURIComponent(userCode)}`,
    { retryOnUnauthorized: false },
  );
}

export function approveCliAuthorization(userCode: string): Promise<CliAuthorizationDecision> {
  return apiRequest<CliAuthorizationDecision>(
    `/v1/auth/cli/authorizations/${encodeURIComponent(userCode)}/approve`,
    { method: "POST", body: {} },
  );
}

export function denyCliAuthorization(userCode: string): Promise<CliAuthorizationDecision> {
  return apiRequest<CliAuthorizationDecision>(
    `/v1/auth/cli/authorizations/${encodeURIComponent(userCode)}/deny`,
    { method: "POST", body: {} },
  );
}

export function fetchMe(): Promise<ActorContext> {
  return apiRequest<ActorContext>("/v1/auth/me");
}

export function revokeSession(): Promise<void> {
  return apiRequest<void>("/v1/auth/session/revoke", { method: "POST", body: {} });
}
