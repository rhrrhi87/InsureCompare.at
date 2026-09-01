// File: frontend/src/types/domain.ts
//
// Type definitions mirroring the backend Pydantic schemas.
// Kept hand-written for clarity; can be replaced by generated types
// from /openapi.json without changing usage sites.

export type ProductLine = "car" | "household" | "travel" | "legal";
export type RiskLevel = "low" | "medium" | "high";
export type RiskTolerance = "low" | "medium" | "high";
export type CoverageLevel = "basic" | "standard" | "comprehensive";
export type DeductiblePreference = "low" | "medium" | "high";
export type UploadStatus = "queued" | "processing" | "ready" | "failed";
export type ClauseType =
  | "coverage"
  | "exclusion"
  | "limit"
  | "deductible"
  | "obligation"
  | "definition"
  | "territorial_scope"
  | "duration"
  | "optional_benefit"
  | "other";
export type ExtractionMethod = "seed" | "ocr_nlp" | "manual";
export type UserRole = "user" | "admin";

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
}

export interface RiskProfile {
  id: number;
  user_id: number;
  insurance_type: ProductLine;
  monthly_budget_eur: number;
  risk_tolerance: RiskTolerance;
  coverage_level: CoverageLevel;
  deductible_preference: DeductiblePreference;
  household_size: number;
  property_value_eur: number | null;
  required_coverages: string[];
  weights: Record<string, number>;
}

export interface Provider {
  id: number;
  name: string;
  country: string;
  logo_url: string | null;
  rating_score: number;
  is_active: boolean;
  created_at: string;
}

export interface Policy {
  id: number;
  provider_id: number;
  provider?: Provider | null;
  name: string;
  product_line: ProductLine;
  monthly_premium_eur: number;
  annual_premium_eur: number;
  deductible_eur: number;
  coverage_limit_eur: number;
  risk_level: RiskLevel;
  coverage_items: string[];
  additional_features: string[];
  exclusions: string[];
  description: string | null;
  is_active: boolean;
  created_at: string;
  retired_at: string | null;
  is_demo_data: boolean;
  document_title: string | null;
  document_type: string | null;
  source_url: string | null;
  source_organisation: string | null;
  retrieval_date: string | null;
  last_reviewed_date: string | null;
  document_language: string;
}

export interface SourceClause {
  id: number;
  clause_type: ClauseType;
  label: string | null;
  text: string;
  document_language: string;
  page_number: number | null;
  confidence: number;
  extraction_method: ExtractionMethod;
}

export interface FeatureContribution {
  feature: string;
  weight: number;
  value: number;
  contribution: number;
  direction: "positive" | "negative";
  label: string;
}

export interface ScoredPolicy {
  policy: Policy;
  score: number;
  breakdown: Record<string, number>;
  contributions: FeatureContribution[];
  narrative: string;
}

export interface CounterfactualExplanation {
  current_policy_id: number;
  current_policy_name: string;
  alternative_policy_id: number;
  alternative_policy_name: string;
  changed_feature: string;
  direction: "increase" | "decrease";
  current_weight: number;
  suggested_weight: number;
  adjusted_weights: Record<string, number>;
  current_policy_score: number;
  alternative_policy_score: number;
  score_margin: number;
}

export interface RecommendationResponse {
  id: number | null;
  product_line: ProductLine;
  weights: Record<string, number>;
  top_pick: ScoredPolicy;
  ranked_policies: ScoredPolicy[];
  counterfactual: CounterfactualExplanation | null;
  rationale: string;
  created_at: string | null;
}

export interface UploadOut {
  id: number;
  user_id: number;
  filename: string;
  content_type: string;
  size_bytes: number;
  status: UploadStatus;
  ocr_confidence: number | null;
  extracted: ExtractedDocument | null;
  error_message: string | null;
  created_at: string;
}

export interface ExtractedClause {
  clause_type: ClauseType;
  label: string | null;
  text: string;
  confidence: number;
  page_number: number | null;
}

export interface ExtractedDocument {
  detected_provider: string | null;
  detected_product_line: string | null;
  monthly_premium_eur: number | null;
  annual_premium_eur: number | null;
  deductible_eur: number | null;
  coverage_limit_eur: number | null;
  coverages: string[];
  exclusions: string[];
  clauses: ExtractedClause[];
  raw_text_excerpt: string | null;
}

export interface CompareSummary {
  cheapest_monthly_eur: number;
  average_monthly_eur: number;
  within_budget_count: number;
  low_risk_count: number;
}

export interface CompareResponse {
  policies: Policy[];
  summary: CompareSummary;
}

export interface AdminStats {
  total_users: number;
  total_policies: number;
  total_uploads: number;
  total_recommendations: number;
}

export interface AuditLogEntry {
  id: number;
  actor_id: number | null;
  actor_email: string | null;
  action: string;
  entity_type: string | null;
  entity_id: number | null;
  payload: Record<string, unknown> | null;
  created_at: string;
}

// ---------- AI Policy Advisor ----------
export interface AdvisorEvidenceRef {
  clause_id: number;
  clause_type: string;
  text: string;
  page_number: number | null;
  confidence: number;
  provenance: string;
}

export interface AdvisorSummary {
  insurer: string | null;
  insurance_type: string | null;
  product_name: string | null;
  main_coverages: string[];
  important_exclusions: string[];
  deductible: string | null;
  coverage_limits: string | null;
  territorial_scope: string | null;
  major_conditions: string[];
  strengths: string[];
  attention_points: string[];
  evidence_ids: number[];
}

export interface AdvisorDocumentRef {
  document_title: string;
  detected_insurer: string | null;
  detected_product_line: string | null;
}

export interface AdvisorSummaryOut {
  summary: AdvisorSummary | null;
  evidence: AdvisorEvidenceRef[];
  document: AdvisorDocumentRef | null;
  available: boolean;
  unavailable_reason: string | null;
}

export interface AdvisorAnswer {
  answer: string;
  supported: boolean;
  key_points: string[];
  attention_points: string[];
  evidence: AdvisorEvidenceRef[];
  document: AdvisorDocumentRef | null;
  available: boolean;
  unavailable_reason: string | null;
}
