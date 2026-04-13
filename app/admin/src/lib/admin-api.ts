import { cookies } from "next/headers";

export type AdminSession = {
  user: {
    user_id: string;
    email: string;
    role: string;
    display_name: string;
    issued_at: string;
    expires_at: string;
  };
  csrf_token?: string | null;
};

export type ReviewTaskListItem = {
  review_task_id: string;
  candidate_id: string;
  run_id: string;
  country_code: string;
  bank_code: string;
  bank_name: string;
  product_type: string;
  product_name: string;
  review_state: "queued" | "approved" | "rejected" | "edited" | "deferred";
  candidate_state: string;
  validation_status: "pass" | "warning" | "error";
  validation_issue_codes: string[];
  source_confidence: number | null;
  queue_reason_code: string;
  issue_summary: string;
  issue_summary_items: Array<{
    code: string;
    severity: string;
    summary: string;
  }>;
  created_at: string;
  updated_at: string;
};

export type ReviewQueueResponse = {
  items: ReviewTaskListItem[];
  summary: {
    total_items: number;
    active_items: number;
    state_counts: Record<string, number>;
    validation_counts: Record<string, number>;
  };
  applied_filters: {
    states: string[];
    bank_code: string | null;
    product_type: string | null;
    validation_status: string | null;
    created_from: string | null;
    created_to: string | null;
    search: string | null;
    sort_by: string;
    sort_order: "asc" | "desc";
  };
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next_page: boolean;
};

export type ReviewDecisionAction = "approve" | "reject" | "edit_approve" | "defer";

export type RunStatusListItem = {
  run_id: string;
  run_type: string;
  run_status: "started" | "completed" | "failed" | "retried";
  trigger_type: string;
  triggered_by: string | null;
  started_at: string | null;
  completed_at: string | null;
  source_item_count: number;
  candidate_count: number;
  review_queued_count: number;
  success_count: number;
  failure_count: number;
  partial_completion_flag: boolean;
  error_summary: string | null;
  pipeline_stage: string | null;
  correlation_id: string | null;
  retry_of_run_id: string | null;
  retried_by_run_id: string | null;
};

export type RunStatusListResponse = {
  items: RunStatusListItem[];
  summary: {
    total_items: number;
    state_counts: Record<string, number>;
    run_type_counts: Record<string, number>;
    partial_items: number;
  };
  applied_filters: {
    states: string[];
    run_type: string | null;
    partial_only: boolean;
    started_from: string | null;
    started_to: string | null;
    search: string | null;
    sort_by: string;
    sort_order: "asc" | "desc";
  };
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next_page: boolean;
};

export type RunStatusDetailResponse = {
  run: {
    run_id: string;
    run_type: string;
    run_status: "started" | "completed" | "failed" | "retried";
    trigger_type: string;
    triggered_by: string | null;
    source_item_count: number;
    source_scope_count: number;
    success_count: number;
    failure_count: number;
    candidate_count: number;
    review_queued_count: number;
    partial_completion_flag: boolean;
    error_summary: string | null;
    retry_of_run_id: string | null;
    retried_by_run_id: string | null;
    started_at: string | null;
    completed_at: string | null;
    pipeline_stage: string | null;
    correlation_id: string | null;
    request_id: string | null;
    source_ids: string[];
  };
  source_items: Array<{
    source_document_id: string;
    source_id: string;
    bank_code: string;
    bank_name: string;
    country_code: string;
    source_type: string;
    source_language: string;
    source_url: string | null;
    snapshot_id: string | null;
    fetched_at: string | null;
    parsed_document_id: string | null;
    parse_quality_note: string | null;
    stage_status: string;
    warning_count: number;
    error_count: number;
    error_summary: string | null;
    runtime_notes: string[];
    safe_metadata: Record<string, unknown>;
  }>;
  stage_summaries: Array<{
    stage_name: string;
    stage_label: string;
    stage_status: string;
    execution_count: number;
    success_count: number;
    failure_count: number;
    execution_status_counts: Record<string, number>;
    started_at: string | null;
    completed_at: string | null;
  }>;
  error_events: Array<{
    scope: "run" | "source";
    severity: "warning" | "error";
    summary: string;
    source_document_id: string | null;
    source_id: string | null;
    stage_status: string | null;
    warning_count: number;
    error_count: number;
    runtime_notes: string[];
    source_url: string | null;
  }>;
  usage_summary: {
    usage_record_count: number;
    model_execution_count: number;
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    estimated_cost: number;
    by_stage: Array<{
      stage_name: string;
      stage_label: string;
      usage_record_count: number;
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
      estimated_cost: number;
    }>;
  };
  related_review_tasks: Array<{
    review_task_id: string;
    candidate_id: string;
    review_state: string;
    queue_reason_code: string;
    product_name: string;
    bank_name: string;
    validation_status: string;
    created_at: string | null;
  }>;
};

export type ChangeHistoryListItem = {
  change_event_id: string;
  canonical_product_id: string;
  product_version_id: string | null;
  product_name: string;
  bank_code: string;
  bank_name: string;
  product_type: string;
  subtype_code: string | null;
  change_type: "New" | "Updated" | "Discontinued" | "Reclassified" | "ManualOverride";
  change_reason_code: string | null;
  change_summary: string;
  changed_fields: string[];
  detected_at: string;
  actor_type: "user" | "system";
  actor: {
    user_id: string | null;
    display_name: string | null;
    email: string | null;
    role: string | null;
  };
  version_info: {
    previous_version_no: number | null;
    current_version_no: number | null;
  };
  review_context: {
    review_task_id: string | null;
    review_state: string | null;
    action_type: string | null;
    reason_code: string | null;
    reason_text: string | null;
    diff_summary: string | null;
    decided_at: string | null;
  };
  run_context: {
    run_id: string | null;
    run_type: string | null;
    run_status: string | null;
    correlation_id: string | null;
  };
  audit_context: {
    audit_event_id: string;
    event_type: string;
    diff_summary: string | null;
    occurred_at: string | null;
    actor: {
      user_id: string | null;
      display_name: string | null;
      email: string | null;
      role: string | null;
    };
  } | null;
};

export type ChangeHistoryListResponse = {
  items: ChangeHistoryListItem[];
  summary: {
    total_items: number;
    affected_product_count: number;
    change_type_counts: Record<string, number>;
    manual_override_items: number;
  };
  applied_filters: {
    product_id: string | null;
    bank_code: string | null;
    product_type: string | null;
    change_type: string | null;
    changed_from: string | null;
    changed_to: string | null;
    search: string | null;
    sort_by: string;
    sort_order: "asc" | "desc";
  };
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next_page: boolean;
};

export type AuditLogListItem = {
  audit_event_id: string;
  event_category: "review" | "run" | "publish" | "auth" | "config" | "usage";
  event_type: string;
  occurred_at: string;
  actor_type: "system" | "user" | "service" | "scheduler";
  actor: {
    actor_id: string | null;
    display_name: string | null;
    email: string | null;
    role_snapshot: string | null;
    current_role: string | null;
  };
  target: {
    target_type: string;
    target_id: string;
    display_name: string | null;
  };
  state_transition: {
    previous_state: string | null;
    new_state: string | null;
  };
  reason: {
    reason_code: string | null;
    reason_text: string | null;
  };
  request_context: {
    request_id: string | null;
    ip_address: string | null;
    user_agent: string | null;
  };
  related_context: {
    run_id: string | null;
    run_type: string | null;
    run_status: string | null;
    candidate_id: string | null;
    review_task_id: string | null;
    product_id: string | null;
    publish_item_id: string | null;
    product_name: string | null;
    bank_code: string | null;
    bank_name: string | null;
  };
  diff_summary: string | null;
  source_ref: string | null;
  retention_class: string;
  event_payload: Record<string, unknown>;
};

export type AuditLogListResponse = {
  items: AuditLogListItem[];
  summary: {
    total_items: number;
    category_counts: Record<string, number>;
    actor_type_counts: Record<string, number>;
    user_actor_items: number;
  };
  applied_filters: {
    event_category: string | null;
    event_type: string | null;
    actor_type: string | null;
    target_type: string | null;
    actor_id: string | null;
    target_id: string | null;
    run_id: string | null;
    review_task_id: string | null;
    product_id: string | null;
    publish_item_id: string | null;
    occurred_from: string | null;
    occurred_to: string | null;
    search: string | null;
    sort_by: string;
    sort_order: "asc" | "desc";
  };
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next_page: boolean;
};

export type LlmUsageDashboardResponse = {
  totals: Record<string, unknown>;
  by_model: Record<string, unknown>[];
  by_agent: Record<string, unknown>[];
  by_run: Record<string, unknown>[];
  trend?: Record<string, unknown>[];
  usage_trend?: Record<string, unknown>[];
  anomaly_candidates: Record<string, unknown>[];
  applied_filters?: Record<string, unknown>;
};

export type ReviewEvidenceLink = {
  field_name: string;
  label: string;
  candidate_value: string;
  citation_confidence: number | null;
  evidence_chunk_id: string;
  evidence_excerpt: string | null;
  source_document_id: string | null;
  source_snapshot_id: string | null;
  parsed_document_id: string | null;
  source_url: string | null;
  source_type: string | null;
  source_id: string | null;
  anchor_type: string | null;
  anchor_value: string | null;
  page_no: number | null;
  chunk_index: number | null;
  field_mapping: {
    source_field_name: string | null;
    normalized_value: unknown;
    value_type: string | null;
    extraction_method: string | null;
    extraction_confidence: number | null;
    evidence_chunk_id: string | null;
    normalization_method: string | null;
    source_subtype_label: string | null;
  };
  model_execution_id: string | null;
  anchor_label: string;
};

export type ReviewFieldTraceGroup = {
  field_name: string;
  label: string;
  value: unknown;
  mapping: ReviewEvidenceLink["field_mapping"];
  evidence_count: number;
  has_evidence: boolean;
  evidence_links: ReviewEvidenceLink[];
};

export type ReviewModelExecution = {
  model_execution_id: string;
  stage_name: string;
  stage_label: string;
  agent_name: string;
  model_id: string;
  execution_status: string;
  execution_metadata: Record<string, unknown>;
  started_at: string | null;
  completed_at: string | null;
  usage: {
    llm_usage_id: string | null;
    prompt_tokens: number | null;
    completion_tokens: number | null;
    estimated_cost: number | null;
    usage_mode: string | null;
    provider: string | null;
    recorded_at: string | null;
    usage_metadata: Record<string, unknown>;
  };
};

export type ReviewTaskDetailResponse = {
  review_task: {
    review_task_id: string;
    candidate_id: string;
    run_id: string;
    product_id: string | null;
    review_state: "queued" | "approved" | "rejected" | "edited" | "deferred";
    queue_reason_code: string;
    issue_summary: string;
    issue_summary_items: Array<{
      code: string;
      severity: string;
      summary: string;
    }>;
    created_at: string;
    updated_at: string;
  };
  candidate: {
    source_document_id: string;
    country_code: string;
    bank_code: string;
    bank_name: string;
    product_family: string;
    product_type: string;
    subtype_code: string | null;
    product_name: string;
    source_language: string;
    currency: string;
    candidate_state: string;
    validation_status: "pass" | "warning" | "error";
    validation_issue_codes: string[];
    source_confidence: number | null;
    review_reason_code: string | null;
    candidate_payload: Record<string, unknown>;
    field_mapping_metadata: Record<string, unknown>;
    field_items: Array<{
      field_name: string;
      label: string;
      value: unknown;
    }>;
  };
  source_context: {
    source_url: string | null;
    source_type: string | null;
    source_id: string | null;
    snapshot_id: string | null;
    fetched_at: string | null;
    parsed_document_id: string | null;
    parse_quality_note: string | null;
    stage_status: string | null;
    warning_count: number | null;
    error_count: number | null;
    error_summary: string | null;
    runtime_notes: string[];
  };
  proposed_fields: Array<{
    field_name: string;
    label: string;
    value: unknown;
    evidence_count: number;
  }>;
  field_trace_groups: ReviewFieldTraceGroup[];
  evidence_summary: {
    item_count: number;
    field_count: number;
  };
  evidence_links: ReviewEvidenceLink[];
  validation_issues: Array<{
    code: string;
    severity: string;
    summary: string;
  }>;
  model_executions: ReviewModelExecution[];
  current_product: {
    product_id: string;
    status: string;
    current_version_no: number;
    product_name: string;
    product_type: string;
    subtype_code: string | null;
    last_verified_at: string | null;
    last_changed_at: string | null;
    normalized_payload: Record<string, unknown>;
  } | null;
  decision_history: Array<{
    review_decision_id: string;
    action_type: string;
    reason_code: string | null;
    reason_text: string | null;
    diff_summary: string | null;
    override_payload: Record<string, unknown>;
    decided_at: string;
    actor: {
      user_id: string | null;
      display_name: string | null;
      email: string | null;
      role: string | null;
    };
  }>;
  available_actions: ReviewDecisionAction[];
};

type AdminApiResponse<T> = {
  data: T;
};

export function getAdminApiOrigin() {
  return process.env.FPDS_ADMIN_API_ORIGIN ?? "http://localhost:4000";
}

async function fetchAdminData<T>(
  path: string,
  searchParams?: URLSearchParams,
  options?: {
    allowNotFound?: boolean;
  },
): Promise<T | null> {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  const url = new URL(path, getAdminApiOrigin());
  if (searchParams) {
    url.search = searchParams.toString();
  }

  const response = await fetch(url, {
    cache: "no-store",
    headers: cookieHeader ? { cookie: cookieHeader } : {}
  });

  if (response.status === 401) {
    return null;
  }

  if (response.status === 404 && options?.allowNotFound) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`Failed to load admin data from ${path}.`);
  }

  const payload = (await response.json()) as AdminApiResponse<T>;
  return payload.data;
}

export async function fetchAdminSession(): Promise<AdminSession | null> {
  return fetchAdminData<AdminSession>("/api/admin/auth/session");
}

export async function fetchReviewQueue(searchParams: URLSearchParams): Promise<ReviewQueueResponse | null> {
  return fetchAdminData<ReviewQueueResponse>("/api/admin/review-tasks", searchParams);
}

export async function fetchReviewTaskDetail(reviewTaskId: string): Promise<ReviewTaskDetailResponse | null> {
  return fetchAdminData<ReviewTaskDetailResponse>(`/api/admin/review-tasks/${reviewTaskId}`, undefined, { allowNotFound: true });
}

export async function fetchRunStatusList(searchParams: URLSearchParams): Promise<RunStatusListResponse | null> {
  return fetchAdminData<RunStatusListResponse>("/api/admin/runs", searchParams);
}

export async function fetchRunStatusDetail(runId: string): Promise<RunStatusDetailResponse | null> {
  return fetchAdminData<RunStatusDetailResponse>(`/api/admin/runs/${runId}`, undefined, { allowNotFound: true });
}

export async function fetchChangeHistoryList(searchParams: URLSearchParams): Promise<ChangeHistoryListResponse | null> {
  return fetchAdminData<ChangeHistoryListResponse>("/api/admin/change-history", searchParams);
}

export async function fetchAuditLogList(searchParams: URLSearchParams): Promise<AuditLogListResponse | null> {
  return fetchAdminData<AuditLogListResponse>("/api/admin/audit-log", searchParams);
}

export async function fetchLlmUsage(searchParams: URLSearchParams): Promise<LlmUsageDashboardResponse | null> {
  return fetchAdminData<LlmUsageDashboardResponse>("/api/admin/llm-usage", searchParams);
}
