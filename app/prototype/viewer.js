(function () {
  const payload = window.FPDS_VIEWER_PAYLOAD || { run: {}, metrics: {}, candidates: [] };
  const state = {
    selectedCandidateId: payload.candidates[0] ? payload.candidates[0].candidate_id : null,
  };

  document.addEventListener("DOMContentLoaded", () => {
    renderRunMeta();
    renderMetrics();
    renderCandidateRail();
    renderSelectedCandidate();
  });

  function renderRunMeta() {
    const container = document.getElementById("run-meta");
    if (!container) {
      return;
    }
    const run = payload.run || {};
    container.innerHTML = "";
    [
      ["Run ID", run.run_id || "Not available"],
      ["Run State", titleize(run.run_state || "unknown")],
      ["Generated", formatDate(payload.generated_at)],
      ["Source Scope", String(run.source_scope_count || 0)],
      ["Routing Mode", titleize(run.routing_mode || "prototype")],
    ].forEach(([label, value]) => {
      const card = document.createElement("div");
      card.className = "meta-card";
      card.innerHTML =
        '<div class="meta-card__label">' +
        escapeHtml(label) +
        '</div><div class="meta-card__value">' +
        escapeHtml(value) +
        "</div>";
      container.appendChild(card);
    });
  }

  function renderMetrics() {
    const container = document.getElementById("metrics");
    if (!container) {
      return;
    }
    const metrics = payload.metrics || {};
    container.innerHTML = "";
    [
      ["Candidates", metrics.candidate_count || 0, "Normalized candidates in this run"],
      ["Queued", metrics.review_queued_count || 0, "Candidates routed into prototype review"],
      ["Errors", metrics.error_count || 0, "Validation error candidates needing attention"],
      ["Evidence Links", metrics.evidence_link_count || 0, "Chunk-backed citations carried into viewer"],
      ["Avg Confidence", formatConfidence(metrics.average_confidence || 0), "Average source confidence across candidates"],
    ].forEach(([label, value, subtext]) => {
      const card = document.createElement("div");
      card.className = "metric-card";
      card.innerHTML =
        '<div class="metric-card__label">' +
        escapeHtml(label) +
        '</div><div class="metric-card__value">' +
        escapeHtml(String(value)) +
        '</div><div class="metric-card__subtext">' +
        escapeHtml(subtext) +
        "</div>";
      container.appendChild(card);
    });
    const count = document.getElementById("candidate-count");
    if (count) {
      count.textContent = String(metrics.candidate_count || 0);
    }
  }

  function renderCandidateRail() {
    const list = document.getElementById("candidate-list");
    if (!list) {
      return;
    }
    list.innerHTML = "";
    if (!payload.candidates || payload.candidates.length === 0) {
      list.innerHTML = '<div class="empty-state">No candidates were available in the exported payload.</div>';
      return;
    }
    payload.candidates.forEach((candidate) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "candidate-item" + (candidate.candidate_id === state.selectedCandidateId ? " is-active" : "");
      button.innerHTML =
        '<div class="candidate-item__meta">' +
        renderBadge(candidate.validation_status, titleize(candidate.validation_status || "unknown")) +
        renderBadge("info", candidate.product_type || "Unknown type") +
        "</div>" +
        '<div class="candidate-item__title">' +
        escapeHtml(candidate.product_name || "Unnamed candidate") +
        "</div>" +
        '<div class="candidate-item__submeta">' +
        renderPill(candidate.source_id || candidate.source_document_id || "unknown source") +
        renderPill("Confidence " + formatConfidence(candidate.source_confidence || 0)) +
        renderPill((candidate.issue_summary || []).length + " issues") +
        "</div>";
      button.addEventListener("click", () => {
        state.selectedCandidateId = candidate.candidate_id;
        renderCandidateRail();
        renderSelectedCandidate();
      });
      list.appendChild(button);
    });
  }

  function renderSelectedCandidate() {
    const candidate = (payload.candidates || []).find((item) => item.candidate_id === state.selectedCandidateId);
    renderDetailHeader(candidate);
    renderSummary(candidate);
    renderFieldChips(candidate);
    renderIssueList(candidate);
    renderPayloadTable(candidate);
    renderEvidenceList(candidate);
  }

  function renderDetailHeader(candidate) {
    const title = document.getElementById("detail-title");
    const status = document.getElementById("detail-status");
    if (!title || !status) {
      return;
    }
    if (!candidate) {
      title.textContent = "Select a candidate";
      status.innerHTML = "";
      return;
    }
    title.textContent = candidate.product_name;
    status.innerHTML =
      renderBadge(candidate.validation_status, titleize(candidate.validation_status || "unknown")) +
      renderBadge("info", (candidate.review_state || "read_only").replace("_", " "));
  }

  function renderSummary(candidate) {
    const container = document.getElementById("detail-summary");
    if (!container) {
      return;
    }
    container.innerHTML = "";
    if (!candidate) {
      container.innerHTML = '<div class="empty-state">Choose a candidate from the left rail to inspect detail.</div>';
      return;
    }
    [
      ["Source", candidate.source_id || candidate.source_document_id],
      ["Review Task", candidate.review_task_id || "Not queued"],
      ["Confidence", formatConfidence(candidate.source_confidence || 0)],
      ["Fetched", formatDate(candidate.source_context.fetched_at)],
      ["Source Type", titleize(candidate.source_context.source_type || "unknown")],
      ["Currency", candidate.currency || "N/A"],
    ].forEach(([label, value]) => {
      const card = document.createElement("div");
      card.className = "summary-card";
      card.innerHTML =
        '<div class="summary-card__label">' +
        escapeHtml(label) +
        '</div><div class="summary-card__value">' +
        escapeHtml(String(value)) +
        "</div>";
      container.appendChild(card);
    });
  }

  function renderFieldChips(candidate) {
    const container = document.getElementById("field-chips");
    if (!container) {
      return;
    }
    container.innerHTML = "";
    if (!candidate) {
      return;
    }
    const fields = candidate.highlight_fields || [];
    if (fields.length === 0) {
      container.innerHTML = '<div class="empty-state">No highlighted canonical fields were exported.</div>';
      return;
    }
    fields.forEach((field) => {
      const card = document.createElement("div");
      card.className = "field-chip";
      card.innerHTML =
        '<div class="field-chip__label">' +
        escapeHtml(field.label) +
        '</div><div class="field-chip__value">' +
        escapeHtml(stringifyValue(field.value)) +
        "</div>";
      container.appendChild(card);
    });
  }

  function renderIssueList(candidate) {
    const container = document.getElementById("issue-list");
    if (!container) {
      return;
    }
    container.innerHTML = "";
    if (!candidate) {
      return;
    }
    const issues = candidate.issue_summary || [];
    if (issues.length === 0) {
      container.innerHTML = '<div class="empty-state">No validation or routing issues were exported.</div>';
      return;
    }
    issues.forEach((issue) => {
      const card = document.createElement("div");
      card.className = "issue-card";
      card.innerHTML =
        renderBadge(issue.severity === "error" ? "error" : "warning", titleize(issue.code || issue.severity || "issue")) +
        '<div class="issue-card__summary">' +
        escapeHtml(issue.summary || "") +
        "</div>";
      container.appendChild(card);
    });
  }

  function renderPayloadTable(candidate) {
    const container = document.getElementById("payload-table");
    if (!container) {
      return;
    }
    container.innerHTML = "";
    if (!candidate) {
      return;
    }
    const payloadEntries = Object.entries(candidate.candidate_payload || {}).filter((entry) => entry[1] !== null && entry[1] !== "");
    if (payloadEntries.length === 0) {
      container.innerHTML = '<div class="empty-state">No canonical payload values were exported.</div>';
      return;
    }
    payloadEntries.forEach(([key, value]) => {
      const row = document.createElement("div");
      row.className = "payload-row";
      row.innerHTML =
        '<div class="payload-row__key">' +
        escapeHtml(titleize(key)) +
        '</div><div class="payload-row__value">' +
        escapeHtml(stringifyValue(value)) +
        "</div>";
      container.appendChild(row);
    });
  }

  function renderEvidenceList(candidate) {
    const container = document.getElementById("evidence-list");
    if (!container) {
      return;
    }
    container.innerHTML = "";
    if (!candidate) {
      return;
    }
    const evidenceLinks = candidate.evidence_links || [];
    if (evidenceLinks.length === 0) {
      container.innerHTML = '<div class="empty-state">No evidence links were exported for this candidate.</div>';
      return;
    }
    evidenceLinks.forEach((item) => {
      const card = document.createElement("article");
      card.className = "evidence-card";
      card.innerHTML =
        '<div class="candidate-item__meta">' +
        renderBadge("info", item.label || titleize(item.field_name || "field")) +
        renderPill(item.anchor_label || "Chunk anchor") +
        renderPill("Confidence " + formatConfidence(item.citation_confidence || 0)) +
        "</div>" +
        '<div class="field-chip__value">' +
        escapeHtml(stringifyValue(item.candidate_value)) +
        "</div>" +
        '<div class="evidence-card__excerpt">' +
        escapeHtml(item.evidence_excerpt || "") +
        "</div>" +
        '<div class="candidate-item__submeta">' +
        renderPill(item.evidence_chunk_id || "chunk") +
        renderPill(candidate.source_context.source_url || "source url unavailable") +
        "</div>";
      container.appendChild(card);
    });
  }

  function renderBadge(tone, label) {
    return '<span class="badge" data-tone="' + escapeHtml(tone || "info") + '">' + escapeHtml(label || "") + "</span>";
  }

  function renderPill(label) {
    return '<span class="pill mono">' + escapeHtml(label || "") + "</span>";
  }

  function formatConfidence(value) {
    return (Number(value || 0) * 100).toFixed(1) + "%";
  }

  function formatDate(value) {
    if (!value) {
      return "N/A";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return String(value);
    }
    return date.toLocaleString("en-CA", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function stringifyValue(value) {
    if (Array.isArray(value) || (value && typeof value === "object")) {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  }

  function titleize(value) {
    return String(value || "")
      .replace(/_/g, " ")
      .replace(/\b\w/g, (token) => token.toUpperCase());
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }
})();
