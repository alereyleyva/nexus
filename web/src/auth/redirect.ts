// Remembers where to send the user after they sign in, so flows that require auth
// (e.g. the CLI approval page) can bounce through /login and back. Persisted in
// sessionStorage so it survives the full-page OIDC redirect round-trip.

const KEY = "nexus.post_login_redirect";

/** Only allow same-origin absolute paths, guarding against open redirects. */
export function safeInternalPath(value: string | null | undefined): string | null {
  if (!value) return null;
  if (!value.startsWith("/") || value.startsWith("//")) return null;
  return value;
}

export function stashPostLoginRedirect(path: string | null | undefined): void {
  const safe = safeInternalPath(path);
  try {
    if (safe) sessionStorage.setItem(KEY, safe);
    else sessionStorage.removeItem(KEY);
  } catch {
    /* storage unavailable — redirect simply falls back to the default */
  }
}

/** Consume the stored redirect target (single use). */
export function takePostLoginRedirect(): string | null {
  try {
    const value = safeInternalPath(sessionStorage.getItem(KEY));
    sessionStorage.removeItem(KEY);
    return value;
  } catch {
    return null;
  }
}
