import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { CheckCircle2 } from "lucide-react";
import { useState } from "react";
import type { FormEvent } from "react";
import { createMemory } from "@/api/memory";
import { ApiError } from "@/api/client";
import type { CreateMemoryRequest, MemoryEntry, MemoryType, VisibilityScope } from "@/api/types";
import { StatusBadge } from "@/components/badges";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, Input, Select, Textarea } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/PageHeader";
import { useProjects } from "@/hooks/useDirectory";
import { MEMORY_TYPES, VISIBILITY_SCOPES } from "@/lib/constants";
import { humanize } from "@/lib/format";

export const Route = createFileRoute("/_app/memory/new")({ component: NewMemoryPage });

const SOURCE_TOOL = "nexus-web";

function NewMemoryPage() {
  const navigate = useNavigate();
  const { projects } = useProjects();

  const [type, setType] = useState<MemoryType>("note");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [rationale, setRationale] = useState("");
  const [visibility, setVisibility] = useState<VisibilityScope>("private");
  const [projectId, setProjectId] = useState("");
  const [groupId, setGroupId] = useState("");
  const [tags, setTags] = useState("");
  const [created, setCreated] = useState<MemoryEntry | null>(null);

  const mutation = useMutation({
    mutationFn: (payload: CreateMemoryRequest) => createMemory(payload),
    onSuccess: (entry) => setCreated(entry),
  });

  const needsProject = visibility === "project";
  const needsGroup = visibility === "group";

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const payload: CreateMemoryRequest = {
      type,
      title: title.trim(),
      body: body.trim(),
      source_tool: SOURCE_TOOL,
      source_kind: "manual",
    };
    if (rationale.trim()) payload.rationale = rationale.trim();
    if (visibility !== "private") payload.visibility_scope = visibility;
    // Project is required for project scope and used as context otherwise.
    if (projectId) payload.project_id = projectId;
    if (needsGroup && groupId.trim()) payload.visibility_group_id = groupId.trim();
    const parsedTags = tags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);
    if (parsedTags.length > 0) payload.tags = parsedTags;
    mutation.mutate(payload);
  };

  if (created) return <CreatedResult entry={created} onReset={() => resetForm()} />;

  function resetForm() {
    setCreated(null);
    setTitle("");
    setBody("");
    setRationale("");
    setTags("");
    mutation.reset();
  }

  const error =
    mutation.error instanceof ApiError
      ? mutation.error.problem?.detail ?? mutation.error.message
      : mutation.error
        ? "Could not reach the API."
        : null;

  return (
    <div className="max-w-3xl">
      <PageHeader
        eyebrow="Capture"
        title="New memory"
        description="Add a memory entry. Shared scopes may be proposed for review; the API decides the outcome."
        actions={
          <Link to="/memory">
            <Button variant="ghost">Cancel</Button>
          </Link>
        }
      />

      <Card className="p-6">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Type">
              <Select value={type} onChange={(e) => setType(e.target.value as MemoryType)}>
                {MEMORY_TYPES.map((value) => (
                  <option key={value} value={value}>
                    {humanize(value)}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Visibility">
              <Select
                value={visibility}
                onChange={(e) => setVisibility(e.target.value as VisibilityScope)}
              >
                {VISIBILITY_SCOPES.map((value) => (
                  <option key={value} value={value}>
                    {humanize(value)}
                  </option>
                ))}
              </Select>
            </Field>
          </div>

          <Field label="Title">
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Short, descriptive title"
              required
              autoFocus
            />
          </Field>

          <Field label="Body">
            <Textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="What should the team remember?"
              rows={6}
              required
            />
          </Field>

          <Field label="Rationale (optional)">
            <Textarea
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              placeholder="Why this decision or note matters"
              rows={3}
            />
          </Field>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label={needsProject ? "Project (required)" : "Project (context, optional)"}>
              <Select value={projectId} onChange={(e) => setProjectId(e.target.value)}>
                <option value="">No project</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.key} — {project.name}
                  </option>
                ))}
              </Select>
            </Field>
            {needsGroup && (
              <Field label="Visibility group ID (required)">
                <Input
                  value={groupId}
                  onChange={(e) => setGroupId(e.target.value)}
                  placeholder="Group UUID"
                />
              </Field>
            )}
          </div>

          <Field label="Tags (comma separated)">
            <Input
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="payments, onboarding"
            />
          </Field>

          {needsProject && !projectId && (
            <p className="text-sm text-text-muted">Select a project for project-scoped memory.</p>
          )}
          {needsGroup && !groupId.trim() && (
            <p className="text-sm text-text-muted">A visibility group ID is required for group scope.</p>
          )}
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

          <div className="flex gap-2">
            <Button
              type="submit"
              variant="cta"
              disabled={
                mutation.isPending ||
                !title.trim() ||
                !body.trim() ||
                (needsProject && !projectId) ||
                (needsGroup && !groupId.trim())
              }
            >
              {mutation.isPending ? "Saving…" : "Create memory"}
            </Button>
            <Button type="button" variant="ghost" onClick={() => void navigate({ to: "/memory" })}>
              Cancel
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

function CreatedResult({ entry, onReset }: { entry: MemoryEntry; onReset: () => void }) {
  const pending = entry.status === "pending_review";
  return (
    <div className="max-w-3xl">
      <PageHeader eyebrow="Capture" title="New memory" />
      <Card className="p-8 text-center">
        <div className="mx-auto mb-3 flex justify-center text-tertiary">
          <CheckCircle2 className="h-10 w-10" />
        </div>
        <div className="mb-3 flex justify-center">
          <StatusBadge status={entry.status} />
        </div>
        <p className="text-lg font-bold text-primary">
          {pending ? "Memory proposed for review" : "Memory created"}
        </p>
        <p className="mt-1 text-text-muted">
          {pending
            ? "This entry was submitted as a proposal. A reviewer must approve it before it becomes active."
            : "This entry is active and visible to authorized readers."}
        </p>
        <div className="mt-6 flex justify-center gap-2">
          <Link to="/memory/$id" params={{ id: entry.id }}>
            <Button variant="primary">View entry</Button>
          </Link>
          <Button variant="secondary" onClick={onReset}>
            Create another
          </Button>
          <Link to="/memory">
            <Button variant="ghost">Back to memory</Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
