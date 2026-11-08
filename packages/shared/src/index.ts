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

export interface OpportunityItem {
  id: string;
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
  created_at: string;
  updated_at: string;
}

export interface KeysetPaginationResponse<T> {
  items: T[];
  next_cursor: string | null;
  total?: number;
}

export interface HealthCheckResponse {
  status: 'ok' | 'degraded';
  db: 'connected' | 'disconnected';
  redis: 'connected' | 'disconnected';
  version: string;
  timestamp: string;
}

