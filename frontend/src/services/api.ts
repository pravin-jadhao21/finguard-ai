/// <reference types="vite/client" />

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `Request failed: ${res.status}` }));
    throw new Error(err.detail || `Error ${res.status}`);
  }
  return res.json();
}

function post<T>(url: string, body: unknown): Promise<T> {
  return request<T>(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

function postText<T>(url: string, body: string): Promise<T> {
  return request<T>(url, {
    method: 'POST',
    headers: { 'Content-Type': 'text/plain' },
    body,
  });
}

// ---- Types ----

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp: string;
  active_policy_version: string;
  engine_mode: string;
}

export type DecisionType = 'ALLOW' | 'REDACT' | 'TOKENIZE' | 'REDIRECT' | 'BLOCK' | 'ESCALATE' | 'MODIFY';

export interface MatchedRule {
  rule_id: string;
  rule_name: string;
  category: string;
  action: DecisionType;
  priority: number;
  weight: number;
  matched_substring?: string;
}

export interface InboundAnalysisResult {
  request_id: string;
  decision: DecisionType;
  decision_source: string;
  reason_codes: string[];
  risk_score: number;
  risk_level: string;
  risk_triggers: string[];
  policy_id: string;
  policy_version: string;
  matched_rules: MatchedRule[];
  data_protection: {
    candidates_found: number;
    categories: string[];
    traces: Array<{
      candidate_id: string;
      candidate_type: string;
      classification_tier: string;
      start_index: number;
      end_index: number;
      checksum_validated: boolean;
      checksum_passed: boolean | null;
      transformation_applied: string;
      safe_masked_fragment: string;
    }>;
  };
  injection_detection: {
    detected: boolean;
    severity: string;
    matches: Array<{
      rule_id: string;
      category: string;
      severity: string;
      matched_pattern: string;
      reason_code: string;
    }>;
  };
  intent_classification: {
    category: string;
    action: string;
    reason_code: string;
    signal_trace: Record<string, unknown>;
    disclaimer: string | null;
  };
  transformed_prompt: string | null;
  original_prompt_length: number;
  redirect_target: string | null;
  explanation: string;
  latency_ms: number;
}

export interface OutboundAnalysisResult {
  request_id: string;
  decision: DecisionType;
  reason_code: string;
  original_response: string;
  sanitized_response: string | null;
  is_modified: boolean;
  leak_detected: boolean;
  unsafe_claim_detected: boolean;
  discrepancy_detected: boolean;
  grounding_details: Array<{
    product_key: string;
    claimed_rate: string | null;
    ground_truth_rate: string | null;
    is_rate_matching: boolean;
  }>;
  fallback_applied: boolean;
  latency_ms: number;
}

export interface EndToEndResult {
  request_id: string;
  final_decision: DecisionType;
  final_response: string;
  inbound: InboundAnalysisResult;
  rag: {
    request_id: string;
    retrieved_count: number;
    authorized_count: number;
    audit_trace: Array<{
      doc_id: string;
      title: string;
      classification: string | null;
      access_decision: string;
      reason_code: string;
    }>;
    latency_ms: number;
  } | null;
  llm_response: {
    raw_response: string;
    model: string;
    is_simulated: boolean;
    matched_topic: string;
    disclaimer: string;
  } | null;
  outbound: OutboundAnalysisResult | null;
  latency_ms: number;
}

export interface PolicyRule {
  id: string;
  name: string;
  category: string;
  action: DecisionType;
  priority: number;
  weight: number;
  reason_code: string;
  condition: {
    pattern?: string | null;
    keywords?: string[] | null;
    max_amount?: number | null;
    required_role?: string | null;
  };
  redirect_target?: string | null;
  replacement_token?: string | null;
  enabled?: boolean;
}

export interface PolicyDefinitionResponse {
  policy_id: string;
  policy_version: string;
  name: string;
  description: string;
  rules_count: number;
  rules: PolicyRule[];
}

export interface PolicyValidationResult {
  valid: boolean;
  policy_id: string | null;
  version: string | null;
  name: string | null;
  rules_count: number;
  errors: string[];
}

export interface PolicyApplyResult {
  status: string;
  policy_id: string;
  version: string;
  name: string;
  rules_count: number;
  previous_versions: number;
}

export interface ToolValidationResponse {
  request_id: string;
  action_decision: DecisionType;
  reason_code: string;
  tool_name: string;
  validated_arguments?: Record<string, unknown>;
  result?: Record<string, unknown>;
  execution_success: boolean;
  latency_ms: number;
}

export interface RAGResponse {
  request_id: string;
  query: string;
  retrieved_count: number;
  authorized_count: number;
  sanitized_context_block: string;
  audit_trace: Array<{
    doc_id: string;
    title: string;
    classification: string | null;
    access_decision: string;
    reason_code: string;
  }>;
  latency_ms: number;
}

export interface AuditLogEntry {
  request_id: string;
  timestamp: string;
  direction: 'INBOUND' | 'OUTBOUND';
  policy_id: string;
  policy_version: string;
  decision: string;
  reason_code: string;
  matched_rule_id?: string;
  risk_metadata: {
    risk_score: number;
    risk_level: string;
    triggers: string[];
  };
  latency_ms: number;
  fallback_active: boolean;
}

export interface EvalCaseResult {
  case_id: string;
  scenario_category: string;
  is_attack: boolean;
  input: string;
  expected_decision: string;
  actual_decision: string;
  matched_rule: string;
  passed: boolean;
  latency_ms: number;
}

export interface EvalResult {
  evaluation_metadata: {
    dataset_name: string;
    dataset_version: string;
    policy_id: string;
    policy_version: string;
    timestamp: string;
  };
  summary_metrics: {
    total_cases: number;
    passed_cases: number;
    overall_pass_rate: number;
    benign_cases: number;
    attack_cases: number;
    precision: number;
    recall: number;
    f1_score: number;
    false_positive_rate: number;
    false_negative_rate: number;
    mean_latency_ms: number;
    p95_latency_ms: number;
  };
  case_results: EvalCaseResult[];
}

export interface ReviewTicket {
  ticket_id: string;
  request_id: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  policy_id: string;
  policy_version: string;
  reason_code: string;
  risk_score: number;
  risk_level: string;
  reviewer_id?: string;
  reviewer_notes?: string;
  created_at: string;
  updated_at: string;
}

// ---- API Functions ----

export const fetchHealth = () => request<HealthResponse>('/api/v1/health');

export const fetchOverviewStats = () => request<Record<string, unknown>>('/api/v1/overview/stats');

export const analyzeInbound = (prompt: string, opts?: {
  user_role?: string;
  transaction_amount?: number;
  context?: Record<string, unknown>;
}) => post<InboundAnalysisResult>('/api/v1/analyze/inbound', {
  prompt,
  user_role: opts?.user_role || 'RetailCustomer',
  transaction_amount: opts?.transaction_amount,
  context: opts?.context || {},
});

export const analyzeOutbound = (llmResponse: string, opts?: {
  prompt_context?: string;
  ground_truth_version?: string;
}) => post<OutboundAnalysisResult>('/api/v1/analyze/outbound', {
  llm_response: llmResponse,
  prompt_context: opts?.prompt_context || '',
  ground_truth_version: opts?.ground_truth_version || '1.0.0',
});

export const runEndToEnd = (prompt: string, opts?: {
  user_role?: string;
  transaction_amount?: number;
  include_rag?: boolean;
}) => post<EndToEndResult>('/api/v1/demo/end-to-end', {
  prompt,
  user_role: opts?.user_role || 'RetailCustomer',
  transaction_amount: opts?.transaction_amount,
  include_rag: opts?.include_rag || false,
});

export const fetchPolicies = () => request<PolicyDefinitionResponse>('/api/v1/policies');

export const validatePolicy = (yaml: string) => postText<PolicyValidationResult>('/api/v1/policies/validate', yaml);

export const applyPolicy = (yaml: string) => postText<PolicyApplyResult>('/api/v1/policies/apply', yaml);

export const validateTool = (
  toolName: string,
  args: Record<string, unknown>,
  userPrompt: string,
  userContext: { user_id: string; user_role: string; step_up_authenticated: boolean; approval_token?: string },
) => post<ToolValidationResponse>('/api/v1/tool/execute', {
  tool_name: toolName,
  arguments: args,
  user_prompt: userPrompt,
  user_context: userContext,
});

export const retrieveRAG = (query: string, userId: string, userRole: string, topK = 5) =>
  post<RAGResponse>('/api/v1/rag/retrieve', {
    query,
    user_context: { user_id: userId, user_role: userRole },
    top_k: topK,
  });

export const fetchAuditLogs = (filters?: { policy_version?: string; decision?: string; limit?: number }) => {
  const params = new URLSearchParams();
  if (filters?.policy_version) params.set('policy_version', filters.policy_version);
  if (filters?.decision) params.set('decision', filters.decision);
  params.set('limit', String(filters?.limit || 50));
  return request<AuditLogEntry[]>(`/api/v1/audit/logs?${params}`);
};

export const runEvaluation = () => post<EvalResult>('/api/v1/evaluation/run', {});

export const fetchReviewTickets = (status?: string) => {
  const url = status ? `/api/v1/review/queue?status=${status}` : '/api/v1/review/queue';
  return request<ReviewTicket[]>(url);
};

export const transitionTicket = (ticketId: string, newStatus: string, reviewerId: string, notes?: string) =>
  post<ReviewTicket>(`/api/v1/review/queue/${ticketId}/transition`, {
    reviewer_id: reviewerId,
    new_status: newStatus,
    notes: notes || '',
  });

export interface DecisionExplanation {
  request_id: string;
  timestamp: string;
  direction: string;
  policy_id: string;
  policy_version: string;
  decision: string;
  reason_code: string;
  matched_rule_id: string;
  risk_summary: {
    risk_score: number;
    risk_level: string;
    triggers: string[];
  };
  latency_ms: number;
  fallback_active: boolean;
  confidential_data_stored: boolean;
}

export const explainDecision = (requestId: string) =>
  request<DecisionExplanation>(`/api/v1/audit/logs/${encodeURIComponent(requestId)}/explain`);

export const fetchPolicyHistory = () =>
  request<{ versions: Array<{ policy_id: string; version: string; name: string; rules_count: number }> }>('/api/v1/policies/history');

