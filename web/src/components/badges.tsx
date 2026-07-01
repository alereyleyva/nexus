import {
  AlertTriangle,
  CheckCircle2,
  Eye,
  FileText,
  FlaskConical,
  HelpCircle,
  ListTodo,
  Lightbulb,
  Lock,
  ShieldAlert,
  Sparkles,
  Users,
} from "lucide-react";
import type { ComponentType } from "react";
import { Badge } from "@/components/ui/Badge";
import { humanize } from "@/lib/format";
import type { MemoryStatus, MemoryType, VisibilityScope } from "@/api/types";

type Tone = "neutral" | "primary" | "teal" | "green" | "amber" | "red" | "slate";

const STATUS_TONE: Record<MemoryStatus, Tone> = {
  active: "green",
  needs_review: "amber",
  pending_review: "teal",
  rejected: "red",
  deprecated: "slate",
  archived: "slate",
};

export function StatusBadge({ status }: { status: MemoryStatus }) {
  return <Badge tone={STATUS_TONE[status]}>{humanize(status)}</Badge>;
}

const TYPE_ICON: Record<MemoryType, ComponentType<{ className?: string }>> = {
  decision: Sparkles,
  problem: AlertTriangle,
  solution: Lightbulb,
  failed_attempt: FlaskConical,
  procedure: ListTodo,
  risk: ShieldAlert,
  open_question: HelpCircle,
  task: CheckCircle2,
  note: FileText,
};

export function TypeBadge({ type }: { type: MemoryType }) {
  const Icon = TYPE_ICON[type];
  return (
    <Badge tone="primary">
      <Icon className="h-3.5 w-3.5" />
      {humanize(type)}
    </Badge>
  );
}

const VISIBILITY_ICON: Record<VisibilityScope, ComponentType<{ className?: string }>> = {
  private: Lock,
  restricted: Eye,
  group: Users,
  project: Users,
  organization: Users,
};

export function VisibilityBadge({ scope }: { scope: VisibilityScope }) {
  const Icon = VISIBILITY_ICON[scope];
  return (
    <Badge tone="teal">
      <Icon className="h-3.5 w-3.5" />
      {humanize(scope)}
    </Badge>
  );
}
