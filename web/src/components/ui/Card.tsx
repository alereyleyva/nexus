import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  interactive?: boolean;
}

export function Card({ className, children, interactive, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-card bg-surface p-8 shadow-sm",
        interactive && "transition-signature hover:-translate-y-px hover:shadow-md",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
