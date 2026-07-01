import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, GitCommitVertical } from "lucide-react";
import type { ReactNode } from "react";
import { archiveMemory, deprecateMemory, getMemory, markNeedsReview } from "@/api/memory";
import type { MemoryEntry } from "@/api/types";
import { ApiError } from "@/api/client";
import { StatusBadge, TypeBadge, VisibilityBadge } from "@/components/badges";
import { EvidenceList } from "@/components/EvidenceList";
import { SourceContextView } from "@/components/SourceContextView";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ErrorState, LoadingBlock } from "@/components/ui/feedback";
import { useProjects, useUsersDirectory } from "@/hooks/useDirectory";
import { formatDate } from "@/lib/format";

export const Route = createFileRoute("/_app/memory/$id")({ component: MemoryDetailPage });

function MemoryDetailPage() {
  const { id } = Route.useParams();
  const query = useQuery({ queryKey: ["memory", id], queryFn: () => getMemory(id) });

  if (query.isLoading) return <LoadingBlock />;
  if (query.isError) return <ErrorState error={query.error} />;
  if (!query.data) return null;
  return <MemoryDetail memory={query.data} />;
}

function MemoryDetail({ memory }: { memory: MemoryEntry }) {
  const queryClient = useQueryClient();
  const { nameOf: ownerName } = useUsersDirectory();
  const { nameOf: projectName, keyOf } = useProjects();

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["memory"] });
    void queryClient.invalidateQueries({ queryKey: ["review-queue"] });
  };

  const lifecycle = useMutation({
    mutationFn: (action: "needs_review" | "deprecate" | "archive") => {
      if (action === "needs_review") return markNeedsReview(memory.id);
      if (action === "deprecate") return deprecateMemory(memory.id);
      return archiveMemory(memory.id);
    },
    onSuccess: invalidate,
  });

  const actionError =
    lifecycle.error instanceof ApiError
      ? (lifecycle.error.problem?.detail ?? lifecycle.error.message)
      : null;

  return (
    <div>
      <Link to="/memory" className="mb-4 inline-flex items-center gap-1 text-sm text-secondary">
        <ArrowLeft className="h-4 w-4" /> Back to Project Memory
      </Link>

      {memory.needs_review_warning && (
        <div className="mb-4 flex items-center gap-2 rounded-card bg-accent/25 px-4 py-3 text-on-accent">
          <AlertTriangle className="h-5 w-5" />
          <span className="text-sm font-bold">
            This memory is marked as needing review — treat it as potentially stale.
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
        <div className="flex flex-col gap-6">
          <Card>
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <TypeBadge type={memory.type} />
              <StatusBadge status={memory.status} />
              <VisibilityBadge scope={memory.visibility_scope} />
            </div>
            <h1 className="text-2xl font-extrabold tracking-tight text-primary">{memory.title}</h1>
            <p className="mt-4 whitespace-pre-wrap text-text">{memory.body}</p>
            {memory.rationale && (
              <div className="mt-5 border-l-2 border-teal pl-4">
                <p className="eyebrow mb-1 text-text-muted">Rationale</p>
                <p className="text-text">{memory.rationale}</p>
              </div>
            )}
            {memory.tags.length > 0 && (
              <div className="mt-5 flex flex-wrap gap-1.5">
                {memory.tags.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-xl bg-background px-2.5 py-1 text-xs font-bold text-text"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            )}
          </Card>

          <Card>
            <h2 className="mb-4 text-lg font-bold text-primary">Evidence</h2>
            <EvidenceList evidence={memory.evidence} />
          </Card>

          <Card>
            <h2 className="mb-4 text-lg font-bold text-primary">Source context</h2>
            <SourceContextView context={memory.source_context} />
          </Card>

          <Card>
            <h2 className="mb-4 text-lg font-bold text-primary">Activity</h2>
            <Timeline memory={memory} reviewer={ownerName(memory.reviewed_by_user_id)} />
          </Card>
        </div>

        <aside className="flex flex-col gap-6">
          <Card className="p-6">
            <h2 className="mb-4 text-lg font-bold text-primary">Details</h2>
            <dl className="flex flex-col gap-3 text-sm">
              <Meta label="Project">
                {memory.project_id ? (
                  <span>
                    {keyOf(memory.project_id) ? `${keyOf(memory.project_id)} · ` : ""}
                    {projectName(memory.project_id)}
                  </span>
                ) : (
                  "—"
                )}
              </Meta>
              <Meta label="Owner">{ownerName(memory.owner_user_id)}</Meta>
              <Meta label="Created by">{ownerName(memory.created_by_user_id)}</Meta>
              <Meta label="Source tool">{memory.source_tool}</Meta>
              {memory.source_ref && <Meta label="Source ref">{memory.source_ref}</Meta>}
              {memory.confidence !== null && (
                <Meta label="Confidence">{Math.round(memory.confidence * 100)}%</Meta>
              )}
              <Meta label="Created">{formatDate(memory.created_at)}</Meta>
              <Meta label="Updated">{formatDate(memory.updated_at)}</Meta>
            </dl>
          </Card>

          <Card className="p-6">
            <h2 className="mb-3 text-lg font-bold text-primary">Lifecycle</h2>
            <div className="flex flex-col gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={lifecycle.isPending || memory.status !== "active"}
                onClick={() => lifecycle.mutate("needs_review")}
              >
                Mark needs review
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={
                  lifecycle.isPending ||
                  !(memory.status === "active" || memory.status === "needs_review")
                }
                onClick={() => lifecycle.mutate("deprecate")}
              >
                Deprecate
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={lifecycle.isPending}
                onClick={() => lifecycle.mutate("archive")}
              >
                Archive
              </Button>
            </div>
            {actionError && <p className="mt-3 text-sm text-red-700">{actionError}</p>}
            <p className="mt-3 text-xs text-text-muted">
              Actions require control over this memory; the API enforces permissions.
            </p>
          </Card>
        </aside>
      </div>
    </div>
  );
}

function Meta({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <dt className="text-text-muted">{label}</dt>
      <dd className="text-right font-medium text-text">{children}</dd>
    </div>
  );
}

function Timeline({ memory, reviewer }: { memory: MemoryEntry; reviewer: string }) {
  const events: { label: string; at: string | null; detail?: string }[] = [
    { label: "Created", at: memory.created_at },
  ];
  if (memory.reviewed_at) {
    events.push({
      label: "Reviewed",
      at: memory.reviewed_at,
      detail: memory.review_comment ? `“${memory.review_comment}” — ${reviewer}` : reviewer,
    });
  }
  events.push({ label: "Last updated", at: memory.updated_at });

  return (
    <ol className="flex flex-col gap-4">
      {events.map((event, index) => (
        <li key={`${event.label}-${index}`} className="flex gap-3">
          <GitCommitVertical className="mt-0.5 h-4 w-4 shrink-0 text-teal" />
          <div>
            <p className="text-sm font-bold text-primary">{event.label}</p>
            <p className="text-xs text-text-muted">{formatDate(event.at)}</p>
            {event.detail && <p className="mt-0.5 text-sm text-text">{event.detail}</p>}
          </div>
        </li>
      ))}
    </ol>
  );
}
