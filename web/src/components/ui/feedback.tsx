import { Loader2 } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";
import { ApiError } from "@/api/client";

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn("animate-spin text-secondary", className)} />;
}

export function LoadingBlock({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-text-muted">
      <Spinner className="h-5 w-5" />
      <span>{label}</span>
    </div>
  );
}

export function EmptyState({
  title,
  description,
  icon,
}: {
  title: string;
  description?: string;
  icon?: ReactNode;
}) {
  return (
    <div className="rounded-card border border-dashed border-surface-tint bg-surface-washed px-6 py-14 text-center">
      {icon && <div className="mx-auto mb-3 text-teal">{icon}</div>}
      <p className="text-lg font-bold text-primary">{title}</p>
      {description && <p className="mt-1 text-text-muted">{description}</p>}
    </div>
  );
}

export function ErrorState({ error }: { error: unknown }) {
  const message =
    error instanceof ApiError
      ? error.problem?.detail ?? error.message
      : error instanceof Error
        ? error.message
        : "Something went wrong.";
  return (
    <div className="rounded-card border border-red-200 bg-red-50 px-6 py-8 text-center text-red-700">
      <p className="font-bold">Could not load</p>
      <p className="mt-1 text-sm">{message}</p>
    </div>
  );
}
