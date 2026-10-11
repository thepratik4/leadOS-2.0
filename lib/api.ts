/**
 * LeadOS Typed API Client
 * Interfaces with FastAPI backend at /api/v1
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export type VerificationStatus = "verified" | "partially_verified" | "unverified" | "unknown";
export type ScoreTier = "high" | "medium" | "low";

export interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  app_name: string;
  version: string;
  database: {
    status: string;
    error: string | null;
  };
  search_provider: {
    name: string;
    available: boolean;
    requires_key: boolean;
    message: string;
  };
  ai_assisted_extraction: {
    configured: boolean;
    mode: string;
  };
}

export interface CompanyResponse {
  id: string;
  domain: string;
  name: string;
  industry: string | null;
  country: string | null;
  region: string | null;
  city: string | null;
  employee_range: string | null;
  description: string | null;
  website_url: string | null;
  created_at: string;
  updated_at: string;
  verified_evidence_count: number;
  total_evidence_count: number;
  lead_score: number | null;
  score_tier: ScoreTier | null;
  is_saved: boolean;
}

export interface EvidenceResponse {
  id: string;
  company_id: string;
  claim_type: string;
  claim_value: string;
  source_url: string;
  source_name: string;
  source_category: string;
  source_excerpt: string | null;
  publication_date: string | null;
  retrieval_timestamp: string;
  verification_status: VerificationStatus;
  validation_notes: string | null;
  created_at: string;
}

export interface SignalResponse {
  id: string;
  signal_type: string;
  confidence_score: number;
  summary: string;
  detected_at: string;
  evidence_id: string | null;
}

export interface ScoreBreakdownItem {
  category: string;
  awarded_points: number;
  max_points: number;
  matched: boolean;
  explanation: string;
  evidence_id: string | null;
}

export interface LeadScoreResult {
  total_score: number;
  score_tier: ScoreTier;
  breakdown: ScoreBreakdownItem[];
  matched_criteria: string[];
  missing_evidence: string[];
  data_quality_score: number;
  scoring_notes: string;
}

export interface DiscoveryCandidateItem {
  company: CompanyResponse;
  signals: SignalResponse[];
  evidence: EvidenceResponse[];
  score: LeadScoreResult;
  primary_signal: string | null;
  verification_summary: {
    verified: number;
    partially_verified: number;
    unverified: number;
    unknown: number;
  };
}

export interface DiscoverySearchRequest {
  query: string;
  industry?: string;
  geography?: string;
  employee_range?: string;
  buying_signal?: string;
  limit?: number;
  verify_sources?: boolean;
}

export interface DiscoverySearchResponse {
  search_run_id: string;
  query: string;
  total_candidates: number;
  verified_candidates: number;
  provider: string;
  duration_ms: number;
  candidates: DiscoveryCandidateItem[];
  provider_status: string;
  provider_notice: string | null;
}

export interface SearchRunResponse {
  id: string;
  query: string;
  filters_json: string;
  candidate_count: number;
  provider: string;
  status: string;
  duration_ms: number;
  created_at: string;
}

export interface CompanyDetailResponse extends CompanyResponse {
  evidence: EvidenceResponse[];
  signals: SignalResponse[];
  score_result: LeadScoreResult | null;
}

export interface FactStatement {
  statement: string;
  evidence_id: string | null;
  source_url: string | null;
  source_name: string | null;
  verification_status: string;
}

export interface InferenceStatement {
  inference: string;
  based_on_evidence_ids: string[];
  confidence: "high" | "medium" | "low";
  reasoning: string;
}

export interface CompanyDossierResponse {
  company_id: string;
  company_name: string;
  domain: string;
  verified_facts: FactStatement[];
  unverified_claims: FactStatement[];
  inferences: InferenceStatement[];
  recommendations: string[];
  data_quality_summary: string;
  evidence_items: EvidenceResponse[];
}

export interface OutreachDraftRequest {
  angle?: string;
  recipient_role?: string;
}

export interface OutreachDraftResponse {
  company_id: string;
  company_name: string;
  has_sufficient_evidence: boolean;
  status_reason: string;
  trigger_summary: string | null;
  supporting_evidence_id: string | null;
  supporting_source_url: string | null;
  subject_line: string | null;
  body_text: string | null;
  facts_referenced: string[];
}

export interface SavedLeadResponse {
  id: string;
  company_id: string;
  status: "new" | "in_review" | "contacted" | "qualified" | "disqualified";
  notes: string | null;
  created_at: string;
  updated_at: string;
  company: CompanyResponse | null;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Array<{ field: string; message: string }>;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail: ApiError = { message: `Request failed with status ${res.status}` };
    try {
      const body = await res.json();
      if (body.error && body.error.message) {
        errorDetail = {
          message: body.error.message,
          code: body.error.code,
          details: body.error.details,
        };
      } else if (body.detail) {
        errorDetail = {
          message: typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail),
        };
      }
    } catch {
      // Use fallback errorDetail
    }
    throw errorDetail;
  }
  return res.json();
}

export const api = {
  async getHealth(): Promise<HealthStatus> {
    const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
    return handleResponse<HealthStatus>(res);
  },

  async searchCompanies(req: DiscoverySearchRequest): Promise<DiscoverySearchResponse> {
    const res = await fetch(`${API_BASE}/discovery/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    return handleResponse<DiscoverySearchResponse>(res);
  },

  async getSearchHistory(limit = 15): Promise<SearchRunResponse[]> {
    const res = await fetch(`${API_BASE}/discovery/history?limit=${limit}`, {
      cache: "no-store",
    });
    return handleResponse<SearchRunResponse[]>(res);
  },

  async getCompanyDetails(companyId: string): Promise<CompanyDetailResponse> {
    const res = await fetch(`${API_BASE}/companies/${companyId}`, {
      cache: "no-store",
    });
    return handleResponse<CompanyDetailResponse>(res);
  },

  async getCompanyEvidence(companyId: string): Promise<EvidenceResponse[]> {
    const res = await fetch(`${API_BASE}/companies/${companyId}/evidence`, {
      cache: "no-store",
    });
    return handleResponse<EvidenceResponse[]>(res);
  },

  async verifyClaim(
    companyId: string,
    claim: { claim_type: string; claim_value: string; source_url: string }
  ): Promise<EvidenceResponse> {
    const res = await fetch(`${API_BASE}/companies/${companyId}/evidence/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(claim),
    });
    return handleResponse<EvidenceResponse>(res);
  },

  async getCompanyDossier(companyId: string): Promise<CompanyDossierResponse> {
    const res = await fetch(`${API_BASE}/companies/${companyId}/dossier`, {
      cache: "no-store",
    });
    return handleResponse<CompanyDossierResponse>(res);
  },

  async draftOutreach(
    companyId: string,
    req: OutreachDraftRequest = {}
  ): Promise<OutreachDraftResponse> {
    const res = await fetch(`${API_BASE}/companies/${companyId}/outreach`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    return handleResponse<OutreachDraftResponse>(res);
  },

  async listSavedLeads(): Promise<SavedLeadResponse[]> {
    const res = await fetch(`${API_BASE}/saved-leads`, {
      cache: "no-store",
    });
    return handleResponse<SavedLeadResponse[]>(res);
  },

  async saveLead(req: { company_id: string; notes?: string; status?: string }): Promise<SavedLeadResponse> {
    const res = await fetch(`${API_BASE}/saved-leads`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    return handleResponse<SavedLeadResponse>(res);
  },

  async updateSavedLead(
    savedLeadId: string,
    req: { notes?: string; status?: string }
  ): Promise<SavedLeadResponse> {
    const res = await fetch(`${API_BASE}/saved-leads/${savedLeadId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    return handleResponse<SavedLeadResponse>(res);
  },

  async deleteSavedLead(savedLeadId: string): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/saved-leads/${savedLeadId}`, {
      method: "DELETE",
    });
    return handleResponse<{ success: boolean; message: string }>(res);
  },

  getExportSavedLeadsUrl(): string {
    return `${API_BASE}/saved-leads/export`;
  },
};
