import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { BookMarked, Check, ShieldCheck, Terminal, X } from "lucide-react";
import type { ReactNode } from "react";
import {
  approveCliAuthorization,
  denyCliAuthorization,
  getCliAuthorization,
} from "@/api/auth";
import { ApiError } from "@/api/client";
import { useAuth } from "@/auth/auth";
import { Button } from "@/components/ui/Button";
import { LoadingBlock } from "@/components/ui/feedback";
import { humanize } from "@/lib/format";

interface ApproveSearch {
  code?: string;
}

export const Route = createFileRoute("/cli/approve")({
  validateSearch: (search: Record<string, unknown>): ApproveSearch => ({
    code: typeof search.code === "string" ? search.code : undefined,
  }),
  component: ApprovePage,
});

function ApprovePage() {
  const { code } = Route.useSearch();
  const { status: authStatus } = useAuth();

  if (!code) {
    return (
      <ApproveFrame>
        <Notice
          tone="error"
          title="Missing device code"
          body="Open this page from the link shown by the Nexus CLI, or paste the full verification URL."
        />
      </ApproveFrame>
    );
  }

  return (
    <ApproveFrame>
      <ApproveContent code={code} authenticated={authStatus === "authenticated"} loading={authStatus === "loading"} />
    </ApproveFrame>
  );
}

function ApproveContent({
  code,
  authenticated,
  loading,
}: {
  code: string;
  authenticated: boolean;
  loading: boolean;
}) {
  const query = useQuery({
    queryKey: ["cli-authorization", code],
    queryFn: () => getCliAuthorization(code),
    retry: false,
  });

  const approve = useMutation({ mutationFn: () => approveCliAuthorization(code) });
  const deny = useMutation({ mutationFn: () => denyCliAuthorization(code) });
  const decided = approve.data ?? deny.data;

  if (loading || query.isLoading) return <LoadingBlock label="Loading login request…" />;

  if (query.isError) {
    const notFound = query.error instanceof ApiError && query.error.status === 404;
    return (
      <Notice
        tone="error"
        title={notFound ? "Login request not found" : "Could not load request"}
        body={
          notFound
            ? "This login request is unknown or has expired. Start a new sign-in from the Nexus CLI."
            : query.error instanceof ApiError
              ? query.error.problem?.detail ?? "Please try again."
              : "Could not reach the API."
        }
      />
    );
  }

  const request = query.data;
  if (!request) return null;

  if (decided) {
    const approved = decided.status === "approved";
    return (
      <Notice
        tone={approved ? "success" : "muted"}
        title={approved ? "CLI login approved" : "CLI login denied"}
        body={
          approved
            ? "You can return to your terminal — the Nexus CLI is now signed in."
            : "This login request was denied. Nothing was granted to the CLI."
        }
      />
    );
  }

  if (request.status !== "pending") {
    return (
      <Notice
        tone="muted"
        title={`This request is ${humanize(request.status).toLowerCase()}`}
        body="It can no longer be approved. Start a new sign-in from the Nexus CLI if you still need access."
      />
    );
  }

  const mutationError =
    (approve.error ?? deny.error) instanceof ApiError
      ? ((approve.error ?? deny.error) as ApiError).problem?.detail
      : approve.error || deny.error
        ? "Something went wrong. Please try again."
        : null;
  const busy = approve.isPending || deny.isPending;

  return (
    <div>
      <div className="mb-4 flex items-center gap-2 text-primary">
        <Terminal className="h-5 w-5 text-secondary" />
        <h2 className="text-lg font-bold">Approve CLI sign-in</h2>
      </div>
      <p className="text-sm text-text-muted">
        <strong className="text-text">{request.client_name}</strong> is requesting access to Nexus on
        your behalf. Approve only if you started this from the CLI.
      </p>

      <dl className="mt-5 flex flex-col gap-4">
        <div>
          <dt className="eyebrow mb-1.5 text-text-muted">Requested capabilities</dt>
          <dd className="flex flex-wrap gap-1.5">
            {request.requested_capabilities.length > 0 ? (
              request.requested_capabilities.map((cap) => (
                <span
                  key={cap}
                  className="rounded-xl bg-background px-2 py-0.5 text-xs font-bold text-text"
                >
                  {cap}
                </span>
              ))
            ) : (
              <span className="text-sm text-text-muted">None</span>
            )}
          </dd>
        </div>
        <div>
          <dt className="eyebrow mb-1.5 text-text-muted">Maximum visibility scope</dt>
          <dd className="text-sm font-bold text-text">
            {request.max_visibility_scope ? humanize(request.max_visibility_scope) : "—"}
          </dd>
        </div>
      </dl>

      {!authenticated ? (
        <div className="mt-6 border-t border-surface-tint pt-5">
          <p className="text-sm text-text-muted">
            You need to be signed in to approve this request.
          </p>
          <Link
            to="/login"
            search={{ redirect: `/cli/approve?code=${encodeURIComponent(code)}` }}
            className="mt-3 inline-block"
          >
            <Button variant="primary">Sign in to continue</Button>
          </Link>
        </div>
      ) : (
        <>
          {mutationError && <p className="mt-4 text-sm text-red-700">{mutationError}</p>}
          <div className="mt-6 flex gap-2 border-t border-surface-tint pt-5">
            <Button variant="cta" disabled={busy} onClick={() => approve.mutate()}>
              <Check className="h-4 w-4" /> Approve
            </Button>
            <Button variant="secondary" disabled={busy} onClick={() => deny.mutate()}>
              <X className="h-4 w-4" /> Deny
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

function Notice({
  tone,
  title,
  body,
}: {
  tone: "success" | "error" | "muted";
  title: string;
  body: string;
}) {
  const icon =
    tone === "success" ? (
      <ShieldCheck className="h-8 w-8 text-tertiary" />
    ) : tone === "error" ? (
      <X className="h-8 w-8 text-red-600" />
    ) : (
      <ShieldCheck className="h-8 w-8 text-text-muted" />
    );
  return (
    <div className="text-center">
      <div className="mx-auto mb-3 flex justify-center">{icon}</div>
      <p className="text-lg font-bold text-primary">{title}</p>
      <p className="mt-1 text-sm text-text-muted">{body}</p>
    </div>
  );
}

function ApproveFrame({ children }: { children: ReactNode }) {
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
