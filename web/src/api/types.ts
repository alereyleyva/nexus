// Domain types mirroring the Nexus /v1 API contract (see specs/api/rest-api.md).

export type MemoryType =
  | "decision"
  | "problem"
  | "solution"
  | "failed_attempt"
  | "procedure"
  | "risk"
  | "open_question"
  | "task"
  | "note";

export type MemoryStatus =
  | "pending_review"
  | "active"
  | "needs_review"
  | "rejected"
  | "deprecated"
  | "archived";

export type VisibilityScope = "private" | "restricted" | "group" | "project" | "organization";

export type SourceKind = "ai_cli" | "manual" | "api" | "future_integration";

export type ProjectRole = "viewer" | "contributor" | "reviewer" | "maintainer";

export type EvidenceKind =
  | "quote"
  | "code_reference"
  | "document_reference"
  | "meeting_note"
  | "chat_message"
  | "url"
  | "ticket"
  | "pull_request"
  | "commit"
  | "manual_note";

export interface PageInfo {
  next_cursor: string | null;
  has_more: boolean;
}

export interface AuthProvider {
  id: string;
  label: string;
  type: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token: string;
  refresh_expires_in: number;
  session_id: string;
  org_id: string;
  user_id: string;
  capabilities: string[];
  max_visibility_scope: VisibilityScope | null;
}

export interface ActorContext {
  org_id: string;
  user_id: string;
  session_id: string;
  capabilities: string[];
  max_visibility_scope: VisibilityScope | null;
  client_type: string;
}

export interface Evidence {
  id: string;
  kind: EvidenceKind;
  title: string | null;
  quote: string | null;
  url: string | null;
  locator: Record<string, unknown>;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface MemoryEntry {
  id: string;
  org_id: string;
  project_id: string | null;
  owner_user_id: string;
  created_by_user_id: string;
  submitted_via_session_id: string | null;
  type: MemoryType;
  title: string;
  body: string;
  rationale: string | null;
  status: MemoryStatus;
  visibility_scope: VisibilityScope;
  visibility_group_id: string | null;
  source_kind: SourceKind;
  source_tool: string;
  source_ref: string | null;
  client_entry_id: string | null;
  confidence: number | null;
  tags: string[];
  source_context: Record<string, unknown>;
  metadata: Record<string, unknown>;
  reviewed_by_user_id: string | null;
  review_comment: string | null;
  reviewed_at: string | null;
  review_after: string | null;
  created_at: string;
  updated_at: string;
  evidence_count: number;
  needs_review_warning: boolean;
  evidence: Evidence[];
}

export interface CreateMemoryRequest {
  type: MemoryType;
  title: string;
  body: string;
  rationale?: string;
  visibility_scope?: VisibilityScope;
  project_id?: string;
  visibility_group_id?: string;
  source_tool: string;
  source_kind: SourceKind;
  tags?: string[];
}

export interface MemoryListResponse {
  items: MemoryEntry[];
  page: PageInfo;
}

export interface CliAuthorizationView {
  client_name: string;
  requested_capabilities: string[];
  max_visibility_scope: VisibilityScope | null;
  status: string;
  expires_in: number;
}

export interface CliAuthorizationDecision {
  status: string;
}

export interface MemoryMutationResponse {
  id: string;
  status: MemoryStatus;
  visibility_scope: VisibilityScope;
  requires_review: boolean;
}

export interface ProjectSummary {
  id: string;
  key: string;
  name: string;
  description: string | null;
  status: "active" | "archived";
  owning_group_id: string;
  effective_role: ProjectRole | null;
}

export interface ProjectListResponse {
  items: ProjectSummary[];
  page: PageInfo;
}

export interface SearchResult {
  id: string;
  type: MemoryType;
  title: string;
  body: string;
  status: MemoryStatus;
  visibility_scope: VisibilityScope;
  project_id: string | null;
  tags: string[];
  score: number;
  evidence_count: number;
  needs_review_warning: boolean;
}

export interface SearchResponse {
  results: SearchResult[];
  page: PageInfo;
}

export interface ContextPackItem {
  id: string;
  title: string;
  body: string;
  status: MemoryStatus;
  evidence_count: number;
}

export interface ContextPackItems {
  decisions: ContextPackItem[];
  problems: ContextPackItem[];
  solutions: ContextPackItem[];
  failed_attempts: ContextPackItem[];
  risks: ContextPackItem[];
  procedures: ContextPackItem[];
  open_questions: ContextPackItem[];
  tasks: ContextPackItem[];
  notes: ContextPackItem[];
}

export interface ContextPackWarning {
  type: string;
  message: string;
}

export interface ContextPackResponse {
  project_id: string | null;
  generated_at: string;
  items: ContextPackItems;
  warnings: ContextPackWarning[];
}

export interface AdminUser {
  id: string;
  email: string;
  display_name: string;
  status: "active" | "disabled";
  role: "member" | "knowledge_admin";
  is_org_admin: boolean;
}

export interface AdminUsersResponse {
  items: AdminUser[];
}

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  code: string;
  detail: string;
  request_id: string;
  errors?: { field: string; code: string; message: string }[];
}
