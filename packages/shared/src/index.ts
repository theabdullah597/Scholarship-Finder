export type UserRole = 'student' | 'admin';

export type OpportunityKind = 'scholarship' | 'internship' | 'fellowship' | 'grant';

export type FundingType = 'fully_funded' | 'partially_funded' | 'unfunded' | 'other';

export type OpportunityStatus = 'pending_review' | 'published' | 'archived' | 'rejected';

export type ApplicationStatus =
  | 'saved'
  | 'in_progress'
  | 'submitted'
  | 'interviewing'
  | 'accepted'
  | 'rejected'
  | 'withdrawn';

export interface StudentProfileData {
  id: string;
  full_name?: string | null;
  citizenship?: string | null;
  target_countries: string[];
  fields_of_interest: string[];
  target_degree_level?: string | null;
  timezone: string;
}

export interface UserData {
  id: string;
  email: string;
  role: UserRole;
  is_verified: boolean;
  created_at: string;
  profile?: StudentProfileData | null;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
  user?: UserData;
}

export interface TagItem {
  id: string;
  name: string;
  category?: string | null;
}

export interface OpportunityItem {
  id: string;
  source_id?: string | null;
  kind: OpportunityKind;
  title: string;
  organization: string;
  description: string;
  country: string;
  fields: string[];
  funding_type: FundingType;
  stipend_amount_min?: number | null;
  stipend_amount_max?: number | null;
  stipend_currency?: string | null;
  deadline?: string | null;
  source_url: string;
  canonical_url: string;
  status: OpportunityStatus;
  tags?: TagItem[];
  created_at: string;
  updated_at: string;
}

export interface KeysetPaginationResponse<T> {
  items: T[];
  next_cursor: string | null;
  total_count?: number;
}

export interface OpportunityFilterParams {
  kind?: OpportunityKind;
  country?: string;
  funding?: FundingType;
  field?: string;
  deadline_min?: string;
  deadline_max?: string;
  stipend_min?: number;
  stipend_max?: number;
  include_expired?: boolean;
  sort?: 'created_desc' | 'deadline_asc' | 'deadline_desc';
  cursor?: string;
  limit?: number;
}

export interface OpportunityCreatePayload {
  kind: OpportunityKind;
  title: string;
  organization: string;
  description: string;
  country: string;
  fields: string[];
  funding_type: FundingType;
  stipend_amount_min?: number | null;
  stipend_amount_max?: number | null;
  stipend_currency?: string | null;
  deadline?: string | null;
  source_url: string;
  canonical_url: string;
  tag_ids?: string[];
}

export interface OpportunityPatchPayload {
  kind?: OpportunityKind;
  title?: string;
  organization?: string;
  description?: string;
  country?: string;
  fields?: string[];
  funding_type?: FundingType;
  stipend_amount_min?: number | null;
  stipend_amount_max?: number | null;
  stipend_currency?: string | null;
  deadline?: string | null;
  source_url?: string;
  canonical_url?: string;
  status?: OpportunityStatus;
  tag_ids?: string[];
}

export interface BulkModeratePayload {
  items: Array<{
    id: string;
    action: 'approve' | 'publish' | 'reject' | 'archive';
  }>;
}

export interface AuditLogItem {
  id: string;
  actor_user_id?: string | null;
  action: string;
  target_type: string;
  target_id: string;
  changes?: Record<string, unknown> | null;
  ip_address?: string | null;
  created_at: string;
}

export type SourceType = 'rss' | 'json_api' | 'html_scraper';

export interface SourceItem {
  id: string;
  name: string;
  source_type: SourceType;
  url: string;
  config: Record<string, unknown>;
  is_active: boolean;
  fetch_interval_minutes: number;
  last_run_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface IngestionRunItem {
  id: string;
  source_id: string;
  source_name?: string | null;
  status: 'running' | 'success' | 'partial_failure' | 'failed';
  items_found: number;
  items_created: number;
  items_updated: number;
  items_failed: number;
  error_log?: string | null;
  started_at: string;
  finished_at?: string | null;
}

export interface SearchResultItem {
  opportunity: OpportunityItem;
  score: number;
  reason: string;
}

export interface SearchResponse {
  results: SearchResultItem[];
  cached: boolean;
  fallback: boolean;
  remaining_requests?: number | null;
}

export interface HealthCheckResponse {
  status: 'ok' | 'degraded';
  db: 'connected' | 'disconnected';
  redis: 'connected' | 'disconnected';
  version: string;
  timestamp: string;
}
