import { Link } from "@tanstack/react-router";
import { FileStack, User } from "lucide-react";
import { StatusBadge, TypeBadge, VisibilityBadge } from "@/components/badges";
import { formatDate } from "@/lib/format";
import type { MemoryEntry } from "@/api/types";

export function MemoryCard({
  memory,
  ownerName,
}: {
  memory: MemoryEntry;
  ownerName: string;
}) {
  return (
    <Link
      to="/memory/$id"
      params={{ id: memory.id }}
      className="transition-signature block rounded-card bg-surface p-6 text-text no-underline shadow-sm hover:-translate-y-px hover:shadow-md"
    >
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <TypeBadge type={memory.type} />
        <StatusBadge status={memory.status} />
        <VisibilityBadge scope={memory.visibility_scope} />
      </div>
      <h3 className="text-lg font-bold text-primary">{memory.title}</h3>
      <p className="mt-1 line-clamp-2 text-text-muted">{memory.body}</p>
      {memory.tags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {memory.tags.map((tag) => (
            <span
              key={tag}
              className="rounded-xl bg-background px-2 py-0.5 text-xs font-bold text-text"
            >
              #{tag}
            </span>
          ))}
        </div>
      )}
      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-text-muted">
        <span className="inline-flex items-center gap-1">
          <User className="h-3.5 w-3.5" />
          {ownerName}
        </span>
        <span>via {memory.source_tool}</span>
        {memory.evidence_count > 0 && (
          <span className="inline-flex items-center gap-1">
            <FileStack className="h-3.5 w-3.5" />
            {memory.evidence_count} evidence
          </span>
        )}
        <span className="ml-auto">{formatDate(memory.updated_at)}</span>
      </div>
    </Link>
  );
}
