import type { MemoryStatus, MemoryType, VisibilityScope } from "@/api/types";

export const MEMORY_TYPES: MemoryType[] = [
  "decision",
  "problem",
  "solution",
  "failed_attempt",
  "procedure",
  "risk",
  "open_question",
  "task",
  "note",
];

export const READABLE_STATUSES: MemoryStatus[] = [
  "active",
  "needs_review",
  "pending_review",
  "deprecated",
  "archived",
  "rejected",
];

export const VISIBILITY_SCOPES: VisibilityScope[] = [
  "private",
  "restricted",
  "group",
  "project",
  "organization",
];
