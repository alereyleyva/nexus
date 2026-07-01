import { apiRequest } from "@/api/client";
import type { ContextPackResponse, MemoryType } from "@/api/types";

export interface ContextPackBody {
  project_id?: string | null;
  task?: string;
  query?: string;
  max_items?: number;
  include_types?: MemoryType[];
}

export function generateContextPack(body: ContextPackBody): Promise<ContextPackResponse> {
  return apiRequest<ContextPackResponse>("/v1/context-packs", {
    method: "POST",
    body: { max_items: 20, ...body },
  });
}
