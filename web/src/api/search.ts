import { apiRequest } from "@/api/client";
import type { MemoryStatus, MemoryType, SearchResponse } from "@/api/types";

export interface SearchBody {
  query?: string;
  project_id?: string | null;
  types?: MemoryType[];
  statuses?: MemoryStatus[];
  tags?: string[];
  limit?: number;
  include_evidence?: boolean;
}

export function search(body: SearchBody): Promise<SearchResponse> {
  return apiRequest<SearchResponse>("/v1/search", {
    method: "POST",
    body: { limit: 20, ...body },
  });
}
