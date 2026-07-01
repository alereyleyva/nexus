import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { BookMarked } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { exchangeWebSession } from "@/api/auth";
import { ApiError } from "@/api/client";
import { useAuth } from "@/auth/auth";
import { takePostLoginRedirect } from "@/auth/redirect";
import { LoadingBlock } from "@/components/ui/feedback";

interface CallbackSearch {
  login_code?: string;
  error?: string;
}

export const Route = createFileRoute("/auth/callback")({
  validateSearch: (search: Record<string, unknown>): CallbackSearch => ({
    login_code: typeof search.login_code === "string" ? search.login_code : undefined,
    error: typeof search.error === "string" ? search.error : undefined,
  }),
  component: CallbackPage,
});

function CallbackPage() {
  const { login_code: loginCode, error: providerError } = Route.useSearch();
  const { establishSession } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    if (providerError) {
      setError(`Google sign-in was not completed (${providerError}).`);
      return;
    }
    if (!loginCode) {
      setError("The sign-in response was missing a login code. Please try again.");
      return;
    }

    exchangeWebSession(loginCode)
      .then((tokens) => establishSession(tokens))
      .then(() => {
        const redirect = takePostLoginRedirect();
        if (redirect) window.location.assign(redirect);
        else void navigate({ to: "/memory" });
      })
      .catch((caught) => {
        if (caught instanceof ApiError && caught.status === 401) {
          setError("This sign-in link has expired or was already used. Please sign in again.");
        } else if (caught instanceof ApiError) {
          setError(caught.problem?.detail ?? "Could not complete sign-in.");
        } else {
          setError("Could not reach the API to complete sign-in.");
        }
      });
  }, [loginCode, providerError, establishSession, navigate]);

  return (
    <CallbackFrame>
      {error ? (
        <div className="text-center">
          <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
          <Link
            to="/login"
            className="transition-signature mt-4 inline-block text-sm font-medium text-secondary hover:text-primary"
          >
            Back to sign in
          </Link>
        </div>
      ) : (
        <LoadingBlock label="Completing sign-in…" />
      )}
    </CallbackFrame>
  );
}

function CallbackFrame({ children }: { children: ReactNode }) {
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
