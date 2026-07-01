import { useQuery } from "@tanstack/react-query";
import { listUsersDirectory } from "@/api/users";
import { listProjects } from "@/api/projects";
import type { AdminUser, ProjectSummary } from "@/api/types";

export function useUsersDirectory() {
  const query = useQuery({ queryKey: ["users-directory"], queryFn: listUsersDirectory });
  const byId = new Map<string, AdminUser>((query.data ?? []).map((user) => [user.id, user]));
  const nameOf = (userId: string | null | undefined): string => {
    if (!userId) return "—";
    return byId.get(userId)?.display_name ?? `${userId.slice(0, 8)}…`;
  };
  return { users: query.data ?? [], nameOf, byId };
}

export function useProjects() {
  const query = useQuery({
    queryKey: ["projects"],
    queryFn: async () => (await listProjects()).items,
  });
  const projects = query.data ?? [];
  const byId = new Map<string, ProjectSummary>(projects.map((project) => [project.id, project]));
  const nameOf = (projectId: string | null | undefined): string => {
    if (!projectId) return "—";
    return byId.get(projectId)?.name ?? `${projectId.slice(0, 8)}…`;
  };
  const keyOf = (projectId: string | null | undefined): string | null => {
    if (!projectId) return null;
    return byId.get(projectId)?.key ?? null;
  };
  return { projects, byId, nameOf, keyOf, isLoading: query.isLoading };
}
