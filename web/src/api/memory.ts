import { apiRequest } from "@/api/client";
import type {
  MemoryEntry,
  MemoryListResponse,
  MemoryMutationResponse,
  MemoryStatus,
} from "@/api/types";

export interface ListMemoryParams {
  projectId?: string;
  statuses?: MemoryStatus[];
  limit?: number;
}

export function listMemory(params: ListMemoryParams = {}): Promise<MemoryListResponse> {
  const query = new URLSearchParams();
  if (params.projectId) query.set("project_id", params.projectId);
  for (const status of params.statuses ?? []) query.append("status", status);
  query.set("limit", String(params.limit ?? 100));
  return apiRequest<MemoryListResponse>(`/v1/memory-entries?${query.toString()}`);
}

export function getMemory(id: string): Promise<MemoryEntry> {
  return apiRequest<MemoryEntry>(`/v1/memory-entries/${id}`);
}

export function listReviewQueue(limit = 50): Promise<MemoryListResponse> {
  return apiRequest<MemoryListResponse>(`/v1/review-queue?limit=${limit}`);
}

export function reviewMemory(
  id: string,
  decision: "approve" | "reject",
  reviewComment?: string,
): Promise<MemoryMutationResponse> {
  return apiRequest<MemoryMutationResponse>(`/v1/memory-entries/${id}/review`, {
    method: "POST",
    body: { decision, review_comment: reviewComment || null },
  });
}

export function markNeedsReview(id: string, reason?: string): Promise<MemoryMutationResponse> {
  return apiRequest<MemoryMutationResponse>(`/v1/memory-entries/${id}/mark-needs-review`, {
    method: "POST",
    body: { reason: reason || null },
  });
}

export function deprecateMemory(id: string, reason?: string): Promise<MemoryMutationResponse> {
  return apiRequest<MemoryMutationResponse>(`/v1/memory-entries/${id}/deprecate`, {
    method: "POST",
    body: { reason: reason || null },
  });
}

export function archiveMemory(id: string, reason?: string): Promise<MemoryMutationResponse> {
  return apiRequest<MemoryMutationResponse>(`/v1/memory-entries/${id}/archive`, {
    method: "POST",
    body: { reason: reason || null },
  });
}

export interface UpdateMemoryBody {
  title?: string;
  body?: string;
  rationale?: string;
  tags?: string[];
}

export function updateMemory(id: string, body: UpdateMemoryBody): Promise<MemoryEntry> {
  return apiRequest<MemoryEntry>(`/v1/memory-entries/${id}`, { method: "PATCH", body });
}
