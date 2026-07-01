import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

type Tone = "neutral" | "primary" | "teal" | "green" | "amber" | "red" | "slate";

const TONES: Record<Tone, string> = {
  neutral: "bg-background text-text",
  primary: "bg-primary/10 text-primary",
  teal: "bg-teal/25 text-primary",
  green: "bg-tertiary/20 text-green-deep",
  amber: "bg-accent/30 text-on-accent",
  red: "bg-red-100 text-red-700",
  slate: "bg-surface-tint text-text-muted",
};

export function Badge({
  tone = "neutral",
  children,
  className,
}: {
  tone?: Tone;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-bold",
        TONES[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
