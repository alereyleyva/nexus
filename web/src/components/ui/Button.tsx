import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

type Variant = "primary" | "cta" | "accent" | "secondary" | "ghost";
type Size = "sm" | "md";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-primary text-on-primary hover:bg-secondary shadow-sm hover:-translate-y-px",
  cta: "bg-tertiary text-on-tertiary hover:bg-green-deep shadow-sm hover:-translate-y-px",
  accent: "bg-accent text-on-accent hover:brightness-95 shadow-sm hover:-translate-y-px",
  secondary: "bg-surface-tint text-text hover:bg-teal-soft/50",
  ghost: "bg-transparent text-text hover:bg-surface-tint/60",
};

const SIZES: Record<Size, string> = {
  sm: "text-sm px-3 py-1.5",
  md: "text-base px-6 py-[11px]",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  children: ReactNode;
}

export function Button({
  variant = "primary",
  size = "md",
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "transition-signature inline-flex items-center justify-center gap-2 rounded-md",
        "font-medium disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-secondary",
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
