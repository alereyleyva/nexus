import { ApiError, apiRequest } from "@/api/client";
import type { AdminUser, AdminUsersResponse } from "@/api/types";

// The seeded web user is an org admin, so the admin user directory resolves owner
// and reviewer display names. Non-admin actors gracefully get an empty directory.
export async function listUsersDirectory(): Promise<AdminUser[]> {
  try {
    const response = await apiRequest<AdminUsersResponse>("/v1/admin/users");
    return response.items;
  } catch (error) {
    if (error instanceof ApiError && (error.status === 403 || error.status === 404)) {
      return [];
    }
    throw error;
  }
}
