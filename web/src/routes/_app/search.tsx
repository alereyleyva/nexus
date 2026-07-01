import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { Search as SearchIcon } from "lucide-react";
import { useState } from "react";
import type { FormEvent } from "react";
import { search } from "@/api/search";
import type { MemoryType, SearchResponse } from "@/api/types";
import { StatusBadge, TypeBadge } from "@/components/badges";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, Input, Select } from "@/components/ui/Field";
import { EmptyState, ErrorState } from "@/components/ui/feedback";
import { PageHeader } from "@/components/ui/PageHeader";
import { useProjects } from "@/hooks/useDirectory";
import { MEMORY_TYPES } from "@/lib/constants";
import { humanize } from "@/lib/format";

export const Route = createFileRoute("/_app/search")({ component: SearchPage });

function SearchPage() {
  const { projects } = useProjects();
  const [query, setQuery] = useState("payment sync retries");
  const [projectId, setProjectId] = useState("");
  const [type, setType] = useState<MemoryType | "">("");

  const run = useMutation<SearchResponse>({
    mutationFn: () =>
      search({
        query: query.trim() || undefined,
        project_id: projectId || undefined,
        types: type ? [type] : undefined,
      }),
  });

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    run.mutate();
  };

  return (
    <div>
      <PageHeader
        eyebrow="Discover"
        title="Search"
        description="Full-text search over memory you are authorized to read (POST /v1/search)."
      />

      <form
        onSubmit={handleSubmit}
        className="mb-6 grid grid-cols-1 gap-3 rounded-card bg-surface p-5 shadow-sm sm:grid-cols-[1fr_200px_200px_auto]"
      >
        <Field label="Query">
          <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="idempotency keys" />
        </Field>
        <Field label="Project">
          <Select value={projectId} onChange={(e) => setProjectId(e.target.value)}>
            <option value="">All projects</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.key}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Type">
          <Select value={type} onChange={(e) => setType(e.target.value as MemoryType | "")}>
            <option value="">All types</option>
            {MEMORY_TYPES.map((value) => (
              <option key={value} value={value}>
                {humanize(value)}
              </option>
            ))}
          </Select>
        </Field>
        <div className="flex items-end">
          <Button type="submit" variant="primary" disabled={run.isPending} className="w-full">
            <SearchIcon className="h-4 w-4" />
            {run.isPending ? "Searching…" : "Search"}
          </Button>
        </div>
      </form>

      {run.isError ? (
        <ErrorState error={run.error} />
      ) : run.data ? (
        run.data.results.length === 0 ? (
          <EmptyState
            icon={<SearchIcon className="h-8 w-8" />}
            title="No results"
            description="Try a broader query or a different project."
          />
        ) : (
          <div className="flex flex-col gap-3">
            <p className="text-sm text-text-muted">{run.data.results.length} result(s)</p>
            {run.data.results.map((result) => (
              <Link
                key={result.id}
                to="/memory/$id"
                params={{ id: result.id }}
                className="no-underline"
              >
                <Card interactive className="p-5">
                  <div className="mb-1 flex flex-wrap items-center gap-2">
                    <TypeBadge type={result.type} />
                    <StatusBadge status={result.status} />
                    <span className="ml-auto text-xs font-bold text-secondary">
                      score {result.score.toFixed(2)}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-primary">{result.title}</h3>
                  <p className="mt-1 line-clamp-2 text-sm text-text-muted">{result.body}</p>
                </Card>
              </Link>
            ))}
          </div>
        )
      ) : (
        <p className="text-text-muted">Enter a query to search authorized memory.</p>
      )}
    </div>
  );
}
