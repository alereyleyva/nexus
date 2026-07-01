import { apiRequest } from "@/api/client";
import type { ProjectListResponse } from "@/api/types";

export function listProjects(): Promise<ProjectListResponse> {
  return apiRequest<ProjectListResponse>("/v1/projects?limit=100");
}
