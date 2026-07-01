import { createFileRoute, Navigate, Outlet } from "@tanstack/react-router";
import { useAuth } from "@/auth/auth";
import { AppShell } from "@/components/AppShell";
import { LoadingBlock } from "@/components/ui/feedback";

export const Route = createFileRoute("/_app")({ component: AppLayout });

function AppLayout() {
  const { status } = useAuth();
  if (status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingBlock label="Loading Nexus…" />
      </div>
    );
  }
  if (status === "unauthenticated") return <Navigate to="/login" />;
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}
