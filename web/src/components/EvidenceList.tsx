import { ExternalLink, Quote } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { humanize } from "@/lib/format";
import type { Evidence } from "@/api/types";

export function EvidenceList({ evidence }: { evidence: Evidence[] }) {
  if (evidence.length === 0) {
    return <p className="text-sm text-text-muted">No evidence attached.</p>;
  }
  return (
    <ul className="flex flex-col gap-3">
      {evidence.map((item) => (
        <li key={item.id} className="rounded-lg border border-surface-tint bg-surface-washed p-4">
          <div className="mb-1 flex items-center gap-2">
            <Badge tone="slate">{humanize(item.kind)}</Badge>
            {item.title && <span className="font-bold text-primary">{item.title}</span>}
          </div>
          {item.quote && (
            <p className="flex gap-2 text-sm text-text">
              <Quote className="mt-0.5 h-4 w-4 shrink-0 text-teal" />
              <span className="italic">{item.quote}</span>
            </p>
          )}
          {item.url && (
            <a
              href={item.url}
              target="_blank"
              rel="noreferrer"
              className="mt-1 inline-flex items-center gap-1 text-sm text-secondary"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              {item.url}
            </a>
          )}
          {Object.keys(item.locator).length > 0 && (
            <pre className="mt-2 overflow-x-auto rounded-md bg-surface p-2 text-xs text-text-muted">
              {JSON.stringify(item.locator, null, 2)}
            </pre>
          )}
        </li>
      ))}
    </ul>
  );
}
