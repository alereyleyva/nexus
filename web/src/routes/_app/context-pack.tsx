import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { AlertTriangle, PackageSearch } from "lucide-react";
import { useState } from "react";
import type { FormEvent } from "react";
import { generateContextPack } from "@/api/contextPacks";
import type { ContextPackItem, ContextPackItems, ContextPackResponse } from "@/api/types";
import { StatusBadge } from "@/components/badges";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, Input, Select } from "@/components/ui/Field";
import { ErrorState } from "@/components/ui/feedback";
import { PageHeader } from "@/components/ui/PageHeader";
import { useProjects } from "@/hooks/useDirectory";

export const Route = createFileRoute("/_app/context-pack")({ component: ContextPackPage });

const GROUPS: { key: keyof ContextPackItems; label: string }[] = [
  { key: "decisions", label: "Decisions" },
  { key: "problems", label: "Problems" },
  { key: "solutions", label: "Solutions" },
  { key: "failed_attempts", label: "Failed attempts" },
  { key: "risks", label: "Risks" },
  { key: "procedures", label: "Procedures" },
  { key: "open_questions", label: "Open questions" },
  { key: "tasks", label: "Tasks" },
  { key: "notes", label: "Notes" },
];

function ContextPackPage() {
  const { projects } = useProjects();
  const [projectId, setProjectId] = useState("");
  const [task, setTask] = useState("Continue payment sync retries");
  const [query, setQuery] = useState("payment sync retries idempotency");
  const [maxItems, setMaxItems] = useState(20);

  const run = useMutation<ContextPackResponse>({
    mutationFn: () =>
      generateContextPack({
        project_id: projectId || undefined,
        task: task.trim() || undefined,
        query: query.trim() || undefined,
        max_items: maxItems,
      }),
  });

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    run.mutate();
  };

  const totalItems = run.data
    ? GROUPS.reduce((sum, group) => sum + run.data!.items[group.key].length, 0)
    : 0;

  return (
    <div>
      <PageHeader
        eyebrow="Handover"
        title="Context Pack"
        description="Generate a structured, authorized pack of memory for a task (POST /v1/context-packs)."
      />

      <form
        onSubmit={handleSubmit}
        className="mb-6 grid grid-cols-1 gap-3 rounded-card bg-surface p-5 shadow-sm sm:grid-cols-2"
      >
        <Field label="Project">
          <Select value={projectId} onChange={(e) => setProjectId(e.target.value)}>
            <option value="">All projects</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.key} — {project.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Max items">
          <Input
            type="number"
            min={1}
            max={50}
            value={maxItems}
            onChange={(e) => setMaxItems(Number(e.target.value))}
          />
        </Field>
        <Field label="Task">
          <Input value={task} onChange={(e) => setTask(e.target.value)} />
        </Field>
        <Field label="Query">
          <Input value={query} onChange={(e) => setQuery(e.target.value)} />
        </Field>
        <div className="sm:col-span-2">
          <Button type="submit" variant="cta" disabled={run.isPending}>
            <PackageSearch className="h-4 w-4" />
            {run.isPending ? "Generating…" : "Generate context pack"}
          </Button>
        </div>
      </form>

      {run.isError && <ErrorState error={run.error} />}

      {run.data && (
        <div className="flex flex-col gap-5">
          {run.data.warnings.map((warning, index) => (
            <div
              key={index}
              className="flex items-center gap-2 rounded-card bg-accent/25 px-4 py-3 text-on-accent"
            >
              <AlertTriangle className="h-5 w-5" />
              <span className="text-sm font-bold">{warning.message}</span>
            </div>
          ))}

          {totalItems === 0 ? (
            <Card>
              <p className="text-text-muted">
                No authorized memory matched this task. Try a broader query or another project.
              </p>
            </Card>
          ) : (
            GROUPS.filter((group) => run.data!.items[group.key].length > 0).map((group) => (
              <ContextGroup
                key={group.key}
                label={group.label}
                items={run.data!.items[group.key]}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
}

function ContextGroup({ label, items }: { label: string; items: ContextPackItem[] }) {
  return (
    <section>
      <div className="mb-3 flex items-center gap-2">
        <h2 className="text-lg font-bold text-primary">{label}</h2>
        <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-bold text-primary">
          {items.length}
        </span>
      </div>
      <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
        {items.map((item) => (
          <Link key={item.id} to="/memory/$id" params={{ id: item.id }} className="no-underline">
            <Card interactive className="p-5">
              <div className="mb-1 flex items-center justify-between gap-2">
                <StatusBadge status={item.status} />
                {item.evidence_count > 0 && (
                  <span className="text-xs text-text-muted">{item.evidence_count} evidence</span>
                )}
              </div>
              <h3 className="text-base font-bold text-primary">{item.title}</h3>
              <p className="mt-1 line-clamp-3 text-sm text-text-muted">{item.body}</p>
            </Card>
          </Link>
        ))}
      </div>
    </section>
  );
}
