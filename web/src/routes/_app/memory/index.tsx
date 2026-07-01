import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { LayoutList } from "lucide-react";
import { useMemo, useState } from "react";
import { listMemory } from "@/api/memory";
import type { MemoryStatus, MemoryType, VisibilityScope } from "@/api/types";
import { MemoryCard } from "@/components/MemoryCard";
import { PageHeader } from "@/components/ui/PageHeader";
import { Field, Input, Select } from "@/components/ui/Field";
import { EmptyState, ErrorState, LoadingBlock } from "@/components/ui/feedback";
import { useProjects, useUsersDirectory } from "@/hooks/useDirectory";
import { MEMORY_TYPES, READABLE_STATUSES, VISIBILITY_SCOPES } from "@/lib/constants";
import { humanize } from "@/lib/format";

export const Route = createFileRoute("/_app/memory/")({ component: MemoryPage });

function MemoryPage() {
  const { projects, nameOf: projectName } = useProjects();
  const { nameOf: ownerName, users } = useUsersDirectory();

  const [projectId, setProjectId] = useState<string>("");
  const [status, setStatus] = useState<MemoryStatus | "">("");
  const [type, setType] = useState<MemoryType | "">("");
  const [visibility, setVisibility] = useState<VisibilityScope | "">("");
  const [ownerId, setOwnerId] = useState<string>("");
  const [sourceTool, setSourceTool] = useState<string>("");
  const [tag, setTag] = useState<string>("");

  const statuses = status ? [status] : undefined;
  const query = useQuery({
    queryKey: ["memory", projectId, status],
    queryFn: () => listMemory({ projectId: projectId || undefined, statuses }),
  });

  const filtered = useMemo(() => {
    const items = query.data?.items ?? [];
    return items.filter((memory) => {
      if (type && memory.type !== type) return false;
      if (visibility && memory.visibility_scope !== visibility) return false;
      if (ownerId && memory.owner_user_id !== ownerId) return false;
      if (sourceTool && !memory.source_tool.toLowerCase().includes(sourceTool.toLowerCase()))
        return false;
      if (tag && !memory.tags.some((t) => t.toLowerCase().includes(tag.toLowerCase())))
        return false;
      return true;
    });
  }, [query.data, type, visibility, ownerId, sourceTool, tag]);

  return (
    <div>
      <PageHeader
        eyebrow="Browse"
        title="Project Memory"
        description="Authorized memory across your projects. Server filters by project and status; the rest refine the results."
      />

      <div className="mb-6 grid grid-cols-1 gap-3 rounded-card bg-surface p-5 shadow-sm sm:grid-cols-2 lg:grid-cols-4">
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
        <Field label="Status">
          <Select value={status} onChange={(e) => setStatus(e.target.value as MemoryStatus | "")}>
            <option value="">Default (active + needs review)</option>
            {READABLE_STATUSES.map((value) => (
              <option key={value} value={value}>
                {humanize(value)}
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
        <Field label="Visibility">
          <Select
            value={visibility}
            onChange={(e) => setVisibility(e.target.value as VisibilityScope | "")}
          >
            <option value="">All scopes</option>
            {VISIBILITY_SCOPES.map((value) => (
              <option key={value} value={value}>
                {humanize(value)}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Owner">
          <Select value={ownerId} onChange={(e) => setOwnerId(e.target.value)}>
            <option value="">All owners</option>
            {users.map((user) => (
              <option key={user.id} value={user.id}>
                {user.display_name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Source tool">
          <Input value={sourceTool} onChange={(e) => setSourceTool(e.target.value)} placeholder="codex" />
        </Field>
        <Field label="Tag">
          <Input value={tag} onChange={(e) => setTag(e.target.value)} placeholder="payments" />
        </Field>
      </div>

      {query.isLoading ? (
        <LoadingBlock />
      ) : query.isError ? (
        <ErrorState error={query.error} />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<LayoutList className="h-8 w-8" />}
          title="No memory matches"
          description="Try clearing a filter or choosing a different project."
        />
      ) : (
        <>
          <p className="mb-3 text-sm text-text-muted">
            {filtered.length} {filtered.length === 1 ? "entry" : "entries"}
            {projectId ? ` in ${projectName(projectId)}` : ""}
          </p>
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            {filtered.map((memory) => (
              <MemoryCard key={memory.id} memory={memory} ownerName={ownerName(memory.owner_user_id)} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
