import { Link } from "@tanstack/react-router";
import { BookMarked, LayoutList, LogOut, PackageSearch, Search, ShieldCheck } from "lucide-react";
import type { ComponentType, ReactNode } from "react";
import { cn } from "@/lib/cn";
import { useAuth } from "@/auth/auth";
import { useUsersDirectory } from "@/hooks/useDirectory";

interface NavEntry {
  to: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
}

const NAV: NavEntry[] = [
  { to: "/memory", label: "Project Memory", icon: LayoutList },
  { to: "/review", label: "Review Queue", icon: ShieldCheck },
  { to: "/search", label: "Search", icon: Search },
  { to: "/context-pack", label: "Context Pack", icon: PackageSearch },
];

export function AppShell({ children }: { children: ReactNode }) {
  const { actor, logout } = useAuth();
  const { nameOf } = useUsersDirectory();
  const displayName = actor ? nameOf(actor.user_id) : "—";

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-surface-tint bg-surface/80 backdrop-blur">
        <div className="mx-auto flex max-w-[1180px] items-center justify-between px-6 py-3">
          <Link to="/memory" className="flex items-center gap-2 text-primary no-underline">
            <BookMarked className="h-6 w-6 text-secondary" />
            <span className="text-xl font-extrabold tracking-tight">Nexus</span>
            <span className="hidden text-sm font-medium text-text-muted sm:inline">
              governed shared memory
            </span>
          </Link>
          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-bold text-primary leading-tight">{displayName}</p>
              <p className="text-xs text-text-muted leading-tight">
                {actor ? actor.client_type : ""} session
              </p>
            </div>
            <button
              type="button"
              onClick={() => void logout()}
              className="transition-signature inline-flex items-center gap-1.5 rounded-md bg-surface-tint px-3 py-1.5 text-sm font-medium text-text hover:bg-teal-soft/50"
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-[1180px] gap-8 px-6 py-8">
        <nav className="sticky top-24 hidden h-fit w-52 shrink-0 flex-col gap-1 lg:flex">
          {NAV.map((entry) => (
            <NavItem key={entry.to} {...entry} />
          ))}
        </nav>
        <main className="min-w-0 flex-1">{children}</main>
      </div>

      <nav className="fixed bottom-0 left-0 right-0 z-20 flex justify-around border-t border-surface-tint bg-surface/90 py-1 backdrop-blur lg:hidden">
        {NAV.map((entry) => (
          <NavItem key={entry.to} {...entry} compact />
        ))}
      </nav>
    </div>
  );
}

function NavItem({ to, label, icon: Icon, compact }: NavEntry & { compact?: boolean }) {
  return (
    <Link
      to={to}
      className={cn(
        "transition-signature flex items-center gap-2 rounded-base px-3 py-2 text-sm font-medium text-text no-underline hover:bg-surface-tint",
        compact && "flex-col gap-0.5 text-xs",
      )}
      activeProps={{ className: "bg-primary text-on-primary hover:bg-primary" }}
    >
      <Icon className={cn("h-4 w-4", compact && "h-5 w-5")} />
      <span>{label}</span>
    </Link>
  );
}
