import { createFileRoute, Navigate, useNavigate } from "@tanstack/react-router";
import { BookMarked } from "lucide-react";
import { useEffect, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { fetchProviders, oidcAuthorizeUrl } from "@/api/auth";
import { ApiError } from "@/api/client";
import { useAuth } from "@/auth/auth";
import { stashPostLoginRedirect, takePostLoginRedirect } from "@/auth/redirect";
import { Button } from "@/components/ui/Button";
import { Field, Input } from "@/components/ui/Field";
import { LoadingBlock } from "@/components/ui/feedback";

interface LoginSearch {
  redirect?: string;
}

export const Route = createFileRoute("/login")({
  validateSearch: (search: Record<string, unknown>): LoginSearch => ({
    redirect: typeof search.redirect === "string" ? search.redirect : undefined,
  }),
  component: LoginPage,
});

function goAfterLogin(navigate: (opts: { to: "/memory" }) => Promise<void>): void {
  const redirect = takePostLoginRedirect();
  if (redirect) {
    // Full-page nav preserves arbitrary internal paths (e.g. /cli/approve?code=…)
    // without fighting the typed router; the persisted session survives the reload.
    window.location.assign(redirect);
  } else {
    void navigate({ to: "/memory" });
  }
}

const DEMO_USERS = [
  { email: "avery.stone@example.com", role: "Org Admin" },
  { email: "morgan.reed@example.com", role: "Contributor" },
  { email: "priya.nair@example.com", role: "Viewer" },
];

function LoginPage() {
  const { status, login } = useAuth();
  const navigate = useNavigate();
  const { redirect } = Route.useSearch();
  const [email, setEmail] = useState("avery.stone@example.com");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [providerIds, setProviderIds] = useState<string[] | null>(null);

  useEffect(() => {
    stashPostLoginRedirect(redirect);
  }, [redirect]);

  useEffect(() => {
    let active = true;
    fetchProviders()
      .then(({ providers }) => {
        if (active) setProviderIds(providers.map((provider) => provider.id));
      })
      .catch(() => {
        if (active) setProviderIds([]);
      });
    return () => {
      active = false;
    };
  }, []);

  if (status === "loading") return <LoginFrame><LoadingBlock label="Checking session…" /></LoginFrame>;
  if (status === "authenticated") return <Navigate to="/memory" />;
  if (providerIds === null)
    return <LoginFrame><LoadingBlock label="Loading sign-in options…" /></LoginFrame>;

  const googleEnabled = providerIds.includes("google");
  const devEnabled = providerIds.includes("dev");

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email.trim());
      goAfterLogin(navigate);
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 404) {
        setError("Dev login is disabled. Start the API with NEXUS_DEV_LOGIN=true.");
      } else if (caught instanceof ApiError) {
        setError(caught.problem?.detail ?? "Login failed.");
      } else {
        setError("Could not reach the API. Is it running on the configured URL?");
      }
      setSubmitting(false);
    }
  };

  const signInWithGoogle = () => {
    window.location.assign(oidcAuthorizeUrl());
  };

  return (
    <LoginFrame>
      {googleEnabled && (
        <Button type="button" variant="primary" className="w-full" onClick={signInWithGoogle}>
          Sign in with Google
        </Button>
      )}
      {googleEnabled && devEnabled && (
        <div className="my-5 flex items-center gap-3 text-xs text-text-muted">
          <span className="h-px flex-1 bg-surface-tint" />
          <span className="eyebrow">or dev login</span>
          <span className="h-px flex-1 bg-surface-tint" />
        </div>
      )}
      {devEnabled && (
        <>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Field label="Email">
              <Input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                autoFocus
                required
              />
            </Field>
            {error && (
              <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
            )}
            <Button type="submit" variant="cta" disabled={submitting}>
              {submitting ? "Signing in…" : "Sign in"}
            </Button>
          </form>
          <div className="mt-6 border-t border-surface-tint pt-4">
            <p className="eyebrow mb-2 text-text-muted">Seeded demo users</p>
            <div className="flex flex-col gap-1">
              {DEMO_USERS.map((user) => (
                <button
                  key={user.email}
                  type="button"
                  onClick={() => setEmail(user.email)}
                  className="transition-signature flex items-center justify-between rounded-md px-2 py-1.5 text-left text-sm hover:bg-surface-tint"
                >
                  <span className="font-medium text-primary">{user.email}</span>
                  <span className="text-xs text-text-muted">{user.role}</span>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
      {!googleEnabled && !devEnabled && (
        <p className="rounded-md bg-surface-tint px-3 py-2 text-sm text-text-muted">
          No sign-in methods are configured. Set <code>NEXUS_OIDC_CLIENT_ID</code>/
          <code>NEXUS_OIDC_CLIENT_SECRET</code> for Google, or <code>NEXUS_DEV_LOGIN=true</code>{" "}
          for dev login, then restart the API.
        </p>
      )}
    </LoginFrame>
  );
}

function LoginFrame({ children }: { children: ReactNode }) {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden px-6">
      <div className="pebble -left-24 top-10 h-72 w-72" />
      <div className="pebble -right-16 bottom-0 h-64 w-64 opacity-40" />
      <div className="relative w-full max-w-md">
        <div className="mb-6 flex items-center gap-2 text-primary">
          <BookMarked className="h-8 w-8 text-secondary" />
          <div>
            <p className="text-2xl font-extrabold leading-none tracking-tight">Nexus</p>
            <p className="text-sm text-text-muted">Governed shared memory for AI-assisted teams</p>
          </div>
        </div>
        <div className="rounded-card bg-surface p-8 shadow-lg">{children}</div>
      </div>
    </div>
  );
}
