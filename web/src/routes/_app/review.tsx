import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Pencil, ShieldCheck, X } from "lucide-react";
import { useState } from "react";
import { ApiError } from "@/api/client";
import { listReviewQueue, reviewMemory, updateMemory } from "@/api/memory";
import type { MemoryEntry } from "@/api/types";
import { StatusBadge, TypeBadge, VisibilityBadge } from "@/components/badges";
import { EvidenceList } from "@/components/EvidenceList";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, Input, Textarea } from "@/components/ui/Field";
import { EmptyState, ErrorState, LoadingBlock } from "@/components/ui/feedback";
import { useProjects, useUsersDirectory } from "@/hooks/useDirectory";

export const Route = createFileRoute("/_app/review")({ component: ReviewPage });

function ReviewPage() {
  const query = useQuery({ queryKey: ["review-queue"], queryFn: () => listReviewQueue() });

  return (
    <div>
      <div className="mb-6">
        <p className="eyebrow mb-2 text-tertiary">Governance</p>
        <h1 className="text-3xl font-extrabold tracking-tight text-primary">Review Queue</h1>
        <p className="mt-1 text-text-muted">
          Pending shared memory you are authorized to review. You cannot review your own proposals.
        </p>
      </div>

      {query.isLoading ? (
        <LoadingBlock />
      ) : query.isError ? (
        <ErrorState error={query.error} />
      ) : (query.data?.items.length ?? 0) === 0 ? (
        <EmptyState
          icon={<ShieldCheck className="h-8 w-8" />}
          title="Nothing to review"
          description="The queue is empty. New proposals from contributors will appear here."
        />
      ) : (
        <div className="flex flex-col gap-4">
          {query.data?.items.map((memory) => <ReviewCard key={memory.id} memory={memory} />)}
        </div>
      )}
    </div>
  );
}

function ReviewCard({ memory }: { memory: MemoryEntry }) {
  const queryClient = useQueryClient();
  const { nameOf: ownerName } = useUsersDirectory();
  const { nameOf: projectName } = useProjects();
  const [rejecting, setRejecting] = useState(false);
  const [comment, setComment] = useState("");
  const [editing, setEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState(memory.title);
  const [draftBody, setDraftBody] = useState(memory.body);
  const [draftTags, setDraftTags] = useState(memory.tags.join(", "));

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["review-queue"] });
    void queryClient.invalidateQueries({ queryKey: ["memory"] });
  };

  const review = useMutation({
    mutationFn: (input: { decision: "approve" | "reject"; comment?: string }) =>
      reviewMemory(memory.id, input.decision, input.comment),
    onSuccess: invalidate,
  });

  const edit = useMutation({
    mutationFn: () =>
      updateMemory(memory.id, {
        title: draftTitle,
        body: draftBody,
        tags: draftTags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
      }),
    onSuccess: () => {
      setEditing(false);
      invalidate();
    },
  });

  const error =
    (review.error ?? edit.error) instanceof ApiError
      ? ((review.error ?? edit.error) as ApiError).problem?.detail
      : null;
  const busy = review.isPending || edit.isPending;

  return (
    <Card className="p-6">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <TypeBadge type={memory.type} />
        <StatusBadge status={memory.status} />
        <VisibilityBadge scope={memory.visibility_scope} />
        <span className="ml-auto text-xs text-text-muted">
          {ownerName(memory.owner_user_id)} · via {memory.source_tool}
          {memory.confidence !== null && ` · ${Math.round(memory.confidence * 100)}% confidence`}
        </span>
      </div>

      {editing ? (
        <div className="flex flex-col gap-3">
          <Field label="Title">
            <Input value={draftTitle} onChange={(e) => setDraftTitle(e.target.value)} />
          </Field>
          <Field label="Body">
            <Textarea value={draftBody} onChange={(e) => setDraftBody(e.target.value)} rows={4} />
          </Field>
          <Field label="Tags (comma separated)">
            <Input value={draftTags} onChange={(e) => setDraftTags(e.target.value)} />
          </Field>
          <div className="flex gap-2">
            <Button size="sm" variant="primary" disabled={busy} onClick={() => edit.mutate()}>
              Save edits
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <>
          <h3 className="text-lg font-bold text-primary">{memory.title}</h3>
          <p className="mt-1 whitespace-pre-wrap text-text">{memory.body}</p>
          {memory.rationale && (
            <div className="mt-3 border-l-2 border-teal pl-3">
              <p className="eyebrow mb-0.5 text-text-muted">Rationale</p>
              <p className="text-sm text-text">{memory.rationale}</p>
            </div>
          )}
          <p className="mt-3 text-sm text-text-muted">
            Proposed scope: <strong className="text-text">{memory.visibility_scope}</strong>
            {memory.project_id ? ` · ${projectName(memory.project_id)}` : ""}
          </p>
          {memory.evidence.length > 0 && (
            <details className="mt-3">
              <summary className="cursor-pointer text-sm font-bold text-secondary">
                {memory.evidence.length} evidence item(s)
              </summary>
              <div className="mt-2">
                <EvidenceList evidence={memory.evidence} />
              </div>
            </details>
          )}
        </>
      )}

      {rejecting && !editing && (
        <div className="mt-4">
          <Field label="Rejection comment">
            <Textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Why is this being rejected?"
              rows={2}
            />
          </Field>
        </div>
      )}

      {error && <p className="mt-3 text-sm text-red-700">{error}</p>}

      {!editing && (
        <div className="mt-4 flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="cta"
            disabled={busy}
            onClick={() => review.mutate({ decision: "approve" })}
          >
            <Check className="h-4 w-4" /> Approve
          </Button>
          {rejecting ? (
            <Button
              size="sm"
              variant="accent"
              disabled={busy}
              onClick={() => review.mutate({ decision: "reject", comment })}
            >
              Confirm reject
            </Button>
          ) : (
            <Button size="sm" variant="secondary" disabled={busy} onClick={() => setRejecting(true)}>
              <X className="h-4 w-4" /> Reject
            </Button>
          )}
          <Button size="sm" variant="ghost" disabled={busy} onClick={() => setEditing(true)}>
            <Pencil className="h-4 w-4" /> Edit
          </Button>
        </div>
      )}
    </Card>
  );
}
