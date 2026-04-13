"use client";

import Link from "next/link";

import { Banner1 } from "@/components/banner1";
import { Stats5 } from "@/components/stats5";
import { Button } from "@/components/ui/button";
import type { LlmUsageDashboardResponse } from "@/lib/admin-api";
import { cn } from "@/lib/utils";

export type LlmUsagePageFilters = {
  search: string;
  from: string;
  to: string;
  runId: string;
  agentName: string;
  modelName: string;
  providerName: string;
  stage: string;
};

type LlmUsageSurfaceProps = {
  filters: LlmUsagePageFilters;
  usage: LlmUsageDashboardResponse;
};

type UsageRow = Record<string, unknown>;

export function LlmUsageSurface({ filters, usage }: LlmUsageSurfaceProps) {
  const modelRows = usage.by_model ?? [];
  const agentRows = usage.by_agent ?? [];
  const runRows = usage.by_run ?? [];
  const trendRows = usage.usage_trend ?? usage.trend ?? [];
  const anomalyRows = usage.anomaly_candidates ?? [];
  const totals = usage.totals ?? {};
  const totalTokens = readNumber(totals, ["total_tokens", "token_total", "tokens"]) ?? 0;
  const totalCost = readNumber(totals, ["estimated_cost", "cost_total", "total_cost"]) ?? 0;
  const activeFilterItems = buildActiveFilterItems(filters);
  const topModel = topUsageRow(modelRows);
  const topAgent = topUsageRow(agentRows);
  const topRun = topUsageRow(runRows);
  const latestTrend = trendRows.at(-1) ?? null;
  const leadAnomaly = anomalyRows[0] ?? null;
  const maxTokenVolume = maxTokens(modelRows, agentRows, runRows, trendRows, anomalyRows);

  const statItems = [
    {
      label: "Usage records",
      value: formatCount(readNumber(totals, ["usage_record_count", "record_count", "count"])),
      note: "Protected usage rows define the current dashboard window.",
      tone: "info" as const,
    },
    {
      label: "Total tokens",
      value: formatTokens(totalTokens),
      note: "Prompt and completion volume stay visible at the top of the route.",
      tone: "success" as const,
    },
    {
      label: "Estimated cost",
      value: formatCost(totalCost),
      note: "Cost interpretation stays on the usage route without turning this into billing workflow.",
      tone: "warning" as const,
    },
    {
      label: "Anomaly candidates",
      value: formatCount(readNumber(totals, ["anomaly_candidate_count", "anomaly_count"]), anomalyRows.length),
      note: "Outlier rows remain easy to inspect before they become weekly cost drift.",
      tone: "neutral" as const,
    },
  ];

  return (
    <section className="grid gap-6">
      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm md:p-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">LLM usage dashboard</p>
            <h1 className="mt-3 text-balance text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
              Token, cost, trend, and anomaly triage now live in one operator-facing observability surface.
            </h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground md:text-base">
              This route stays separate from public metrics and billing workflow. It keeps time-window scope, model and
              agent concentration, run-linked spend, trend movement, and anomaly drilldown readable from the same admin
              dashboard.
            </p>
          </div>

          <div className="inline-flex items-center rounded-full bg-success-soft px-3 py-1 text-xs font-medium text-success">
            Usage v1
          </div>
        </div>

        <div className="mt-6">
          <Banner1
            defaultVisible={true}
            description="The page is still read-only and observability-first. Quota controls, budget caps, and alert governance remain separate follow-on operational slices."
            dismissible={false}
            title="Slice boundary"
            tone="info"
          />
        </div>
      </article>

      <Stats5
        className="bg-card/95"
        description="The header now summarizes actual scope coverage, volume, and drift signal instead of only exposing the raw route."
        items={statItems}
        title="Filtered usage snapshot"
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.04fr)_minmax(20rem,0.96fr)]">
        <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
          <div className="grid gap-4 md:grid-cols-2">
            <SignalCard
              label="Coverage"
              note={`${formatCount(readNumber(totals, ["run_count"]))} runs, ${formatCount(readNumber(totals, ["model_count"]))} models, ${formatCount(readNumber(totals, ["agent_count"]))} agents in view.`}
              value={formatCoverage(readText(totals, ["first_recorded_at"]), readText(totals, ["last_recorded_at"]))}
            />
            <SignalCard
              label="Density"
              note={`${formatCost(readNumber(totals, ["average_cost_per_record"]))} average cost per row and ${formatCost(readNumber(totals, ["estimated_cost_per_1k_tokens"]))} per 1k tokens.`}
              value={`${formatTokens(readNumber(totals, ["average_tokens_per_record"]))} avg tokens / row`}
            />
            <SignalCard
              label="Review reach"
              note={`${formatCount(readNumber(totals, ["model_execution_count"]))} model executions and ${formatCount(readNumber(totals, ["zero_token_records"]))} zero-token rows are in view.`}
              value={`${formatCount(readNumber(totals, ["candidate_count"]))} candidate-linked rows`}
            />
            <SignalCard
              label="Active filters"
              note={activeFilterItems.length ? activeFilterItems.join(" / ") : "No scope filters are active in the current window."}
              value={formatCount(activeFilterItems.length)}
            />
          </div>
        </article>

        <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
          <div className="grid gap-3">
            <HotspotCard
              actionHref={topModel ? buildUsageHref(filters, { modelName: readText(topModel, ["model_name"]), runId: "", search: "" }) : ""}
              actionLabel="Focus model"
              label="Top model"
              note={topModel ? rowText(topModel, ["provider_name", "provider_names"], "Provider") : "No model concentration yet."}
              shareValue={topModel ? readNumber(topModel, ["cost_share_percent"]) : null}
              value={topModel ? rowLabel(topModel, "model_name", "Model") : "No model rows"}
            />
            <HotspotCard
              actionHref={topAgent ? buildUsageHref(filters, { agentName: readText(topAgent, ["agent_name"]), runId: "", search: "" }) : ""}
              actionLabel="Focus agent"
              label="Top agent"
              note={topAgent ? rowText(topAgent, ["stage_names"], "No stage context") : "No agent concentration yet."}
              shareValue={topAgent ? readNumber(topAgent, ["cost_share_percent"]) : null}
              value={topAgent ? rowLabel(topAgent, "agent_name", "Agent") : "No agent rows"}
            />
            <HotspotCard
              actionHref={topRun ? rowLinkToRun(topRun) : ""}
              actionLabel="Open run"
              label="Top run"
              note={topRun ? rowText(topRun, ["run_type", "run_state"], "Run context") : "No run concentration yet."}
              shareValue={topRun ? readNumber(topRun, ["cost_share_percent"]) : null}
              value={topRun ? rowLabel(topRun, "run_id", "Run") : "No run rows"}
            />
          </div>

          <div className="mt-4 rounded-[1.5rem] border border-border/80 bg-background p-4">
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">Lead anomaly</p>
            <h2 className="mt-2 text-lg font-semibold tracking-tight text-foreground">
              {leadAnomaly ? rowSummary(leadAnomaly, "No anomaly reason stored.") : "No anomaly candidates in the current scope."}
            </h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              {leadAnomaly
                ? `${rowLabel(leadAnomaly, "run_id", "Run")} / ${rowText(leadAnomaly, ["agent_name", "model_name"], "Context")}`
                : "Broaden the time range or clear some filters if you want to inspect drift candidates."}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {leadAnomaly ? (
                <span className={cn("rounded-full px-3 py-1 text-xs font-medium", anomalyBadgeClasses(leadAnomaly))}>
                  {rowSignal(leadAnomaly)}
                </span>
              ) : null}
              {leadAnomaly && rowLinkToReview(leadAnomaly) ? (
                <Button asChild size="sm" variant="outline">
                  <Link href={rowLinkToReview(leadAnomaly)!}>Open review</Link>
                </Button>
              ) : null}
              {leadAnomaly && rowLinkToRun(leadAnomaly) ? (
                <Button asChild size="sm" variant="outline">
                  <Link href={rowLinkToRun(leadAnomaly)!}>Open run</Link>
                </Button>
              ) : null}
            </div>
          </div>
        </article>
      </div>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <div className="flex flex-col gap-4 border-b border-border/80 pb-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Filters and scope</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">Diagnostic controls</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Search by usage id, run id, request id, product, bank, or review task. Narrow further by provider or
              stage when a drift signal looks concentrated in a specific part of the orchestration chain.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button asChild size="sm" variant="outline">
              <Link href="/admin/usage">Reset scope</Link>
            </Button>
            {filters.search ? (
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                Search {filters.search}
              </span>
            ) : null}
            {filters.runId ? (
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                Run {filters.runId}
              </span>
            ) : null}
            {filters.agentName ? (
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                Agent {filters.agentName}
              </span>
            ) : null}
            {filters.modelName ? (
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                Model {filters.modelName}
              </span>
            ) : null}
            {filters.providerName ? (
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                Provider {filters.providerName}
              </span>
            ) : null}
            {filters.stage ? (
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                Stage {filters.stage}
              </span>
            ) : null}
          </div>
        </div>

        <form action="/admin/usage" className="mt-6 grid gap-5">
          <div className="grid gap-4 xl:grid-cols-[1.3fr_repeat(4,minmax(0,1fr))]">
            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Search</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.search}
                name="q"
                placeholder="usage id, request id, product, review, bank"
                type="search"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">From</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.from}
                name="from"
                type="date"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">To</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.to}
                name="to"
                type="date"
              />
            </label>

            <label className="grid gap-2 text-sm xl:col-span-2">
              <span className="font-medium text-foreground">Run id</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.runId}
                name="run_id"
                placeholder="run id"
                type="text"
              />
            </label>
          </div>

          <div className="grid gap-4 xl:grid-cols-[repeat(5,minmax(0,1fr))_auto]">
            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Agent name</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.agentName}
                name="agent_name"
                placeholder="extraction-agent"
                type="text"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Model name</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.modelName}
                name="model_name"
                placeholder="gpt-4.1-mini"
                type="text"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Provider</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.providerName}
                name="provider_name"
                placeholder="openai"
                type="text"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Stage</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.stage}
                name="stage"
                placeholder="validation_routing"
                type="text"
              />
            </label>

            <div className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Quick scopes</span>
              <div className="flex flex-wrap gap-2">
                <Button asChild size="sm" variant="outline">
                  <Link href={buildUsageHref(filters, { stage: "extraction" })}>Extraction</Link>
                </Button>
                <Button asChild size="sm" variant="outline">
                  <Link href={buildUsageHref(filters, { stage: "normalization" })}>Normalization</Link>
                </Button>
                <Button asChild size="sm" variant="outline">
                  <Link href={buildUsageHref(filters, { stage: "validation_routing" })}>Validation</Link>
                </Button>
              </div>
            </div>

            <div className="flex items-end gap-2">
              <Button type="submit">Apply filters</Button>
              <Button asChild variant="outline">
                <Link href="/admin/usage">Clear</Link>
              </Button>
            </div>
          </div>
        </form>
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
        <div className="flex flex-col gap-3 border-b border-border/80 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Totals</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">Usage totals and density</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Prompt and completion totals stay separate from density and zero-token coverage so operators can quickly
              tell whether a cost spike is volume-driven or context-driven.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {filters.from || filters.to ? (
              <span className="rounded-full bg-warning-soft px-3 py-1 text-xs font-medium text-warning">
                {filters.from || "Start"} to {filters.to || "Now"}
              </span>
            ) : null}
          </div>
        </div>

        <div className="px-6 py-5">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <MetricCard label="Prompt tokens" value={formatTokens(readNumber(totals, ["prompt_tokens"]))} />
            <MetricCard label="Completion tokens" value={formatTokens(readNumber(totals, ["completion_tokens"]))} />
            <MetricCard label="Total tokens" value={formatTokens(readNumber(totals, ["total_tokens", "token_total", "tokens"]))} />
            <MetricCard label="Estimated cost" value={formatCost(readNumber(totals, ["estimated_cost", "cost_total", "total_cost"]))} />
            <MetricCard label="Avg tokens / row" value={formatTokens(readNumber(totals, ["average_tokens_per_record"]))} />
            <MetricCard label="Zero-token rows" value={formatCount(readNumber(totals, ["zero_token_records"]))} />
          </div>
        </div>
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
        <SectionHeader
          eyebrow="By model"
          title="Model concentration"
          description="Model rows now show both raw volume and concentration share so it is easier to spot whether one model is dominating the current cost window."
        />

        {modelRows.length === 0 ? (
          <EmptySection
            title="No model rows"
            copy="The current window returned no by-model aggregation. Broaden the date range or clear the model filter."
          />
        ) : (
          <div className="overflow-x-auto px-6 py-5">
            <table className="min-w-[1440px] table-fixed border-separate border-spacing-0">
              <thead>
                <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                  <th className="border-b border-border px-3 py-3 font-medium">Model</th>
                  <th className="border-b border-border px-3 py-3 font-medium">Scope</th>
                  <th className="border-b border-border px-3 py-3 font-medium">Tokens</th>
                  <th className="border-b border-border px-3 py-3 font-medium">Cost</th>
                  <th className="border-b border-border px-3 py-3 font-medium">Averages</th>
                  <th className="border-b border-border px-3 py-3 font-medium">Last seen</th>
                  <th className="border-b border-border px-3 py-3 font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {modelRows.map((row, index) => (
                  <tr className="align-top" key={rowKey(row, index, ["model_name", "model_id", "name"])}>
                    <td className="border-b border-border/70 px-3 py-4">
                      <div className="grid gap-1">
                        <p className="font-medium text-foreground">{rowLabel(row, "model_name", "Model")}</p>
                        <p className="text-xs text-muted-foreground">{rowLabel(row, "provider_name", "Provider")}</p>
                      </div>
                    </td>
                    <td className="border-b border-border/70 px-3 py-4">
                      <div className="grid gap-1 text-sm">
                        <span className="font-medium text-foreground">
                          {formatCount(readNumber(row, ["usage_record_count", "record_count", "count"]))} rows /{" "}
                          {formatCount(readNumber(row, ["run_count", "run_total"]))} runs
                        </span>
                        <span className="text-muted-foreground">
                          {formatCount(readNumber(row, ["candidate_count"]))} candidates / {rowText(row, ["stage_names"], "No stage context")}
                        </span>
                      </div>
                    </td>
                    <td className="border-b border-border/70 px-3 py-4">
                      <ShareCell
                        maxValue={totalTokens}
                        sharePercent={readNumber(row, ["token_share_percent"]) ?? safeShare(readNumber(row, ["total_tokens"]), totalTokens)}
                        value={formatTokens(readNumber(row, ["total_tokens", "tokens", "token_total"]))}
                      />
                    </td>
                    <td className="border-b border-border/70 px-3 py-4">
                      <ShareCell
                        maxValue={totalCost}
                        sharePercent={readNumber(row, ["cost_share_percent"]) ?? safeShare(readNumber(row, ["estimated_cost"]), totalCost)}
                        tone="warning"
                        value={formatCost(readNumber(row, ["estimated_cost", "cost", "total_cost"]))}
                      />
                    </td>
                    <td className="border-b border-border/70 px-3 py-4">
                      <div className="grid gap-1 text-sm">
                        <span className="font-medium text-foreground">
                          {formatTokens(readNumber(row, ["average_tokens", "avg_tokens"]))} avg tokens
                        </span>
                        <span className="text-muted-foreground">
                          {formatCost(readNumber(row, ["average_cost"]))} avg cost
                        </span>
                      </div>
                    </td>
                    <td className="border-b border-border/70 px-3 py-4 text-sm text-muted-foreground">
                      {formatTimestamp(readText(row, ["last_seen_at", "last_recorded_at", "updated_at", "recorded_at"]))}
                    </td>
                    <td className="border-b border-border/70 px-3 py-4">
                      <Button asChild size="sm" variant="outline">
                        <Link href={buildUsageHref(filters, { modelName: readText(row, ["model_name"]), runId: "", search: "" })}>
                          Focus model
                        </Link>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>

      <div className="grid gap-6 xl:grid-cols-2">
        <article className="rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
          <SectionHeader
            eyebrow="By agent"
            title="Agent concentration"
            description="Agent rows show which orchestration layer is producing the most token and cost pressure in the current window."
          />

          {agentRows.length === 0 ? (
            <EmptySection
              title="No agent rows"
              copy="There is no by-agent aggregation in the current window. Broaden the filters to recover agent context."
            />
          ) : (
            <div className="overflow-x-auto px-6 py-5">
              <table className="min-w-[1220px] table-fixed border-separate border-spacing-0">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                    <th className="border-b border-border px-3 py-3 font-medium">Agent</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Scope</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Tokens</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Cost</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {agentRows.map((row, index) => (
                    <tr className="align-top" key={rowKey(row, index, ["agent_name", "name", "agent_id"])}>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1">
                          <p className="font-medium text-foreground">{rowLabel(row, "agent_name", "Agent")}</p>
                          <p className="text-xs text-muted-foreground">{rowText(row, ["stage_names"], "No stage context")}</p>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1 text-sm">
                          <span className="font-medium text-foreground">
                            {formatCount(readNumber(row, ["usage_record_count", "record_count", "count"]))} rows /{" "}
                            {formatCount(readNumber(row, ["run_count", "run_total"]))} runs
                          </span>
                          <span className="text-muted-foreground">{rowText(row, ["model_names"], "No model context")}</span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <ShareCell
                          maxValue={totalTokens}
                          sharePercent={readNumber(row, ["token_share_percent"]) ?? safeShare(readNumber(row, ["total_tokens"]), totalTokens)}
                          value={formatTokens(readNumber(row, ["total_tokens", "tokens", "token_total"]))}
                        />
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <ShareCell
                          maxValue={totalCost}
                          sharePercent={readNumber(row, ["cost_share_percent"]) ?? safeShare(readNumber(row, ["estimated_cost"]), totalCost)}
                          tone="warning"
                          value={formatCost(readNumber(row, ["estimated_cost", "cost", "total_cost"]))}
                        />
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <Button asChild size="sm" variant="outline">
                          <Link href={buildUsageHref(filters, { agentName: readText(row, ["agent_name"]), runId: "", search: "" })}>
                            Focus agent
                          </Link>
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>

        <article className="rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
          <SectionHeader
            eyebrow="By run"
            title="Run-linked spend"
            description="Run rows keep the highest-cost execution windows one click away from the owning diagnostic route."
          />

          {runRows.length === 0 ? (
            <EmptySection
              title="No run rows"
              copy="There is no by-run aggregation in the current window. Widen the scope or clear the run filter."
            />
          ) : (
            <div className="overflow-x-auto px-6 py-5">
              <table className="min-w-[1280px] table-fixed border-separate border-spacing-0">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                    <th className="border-b border-border px-3 py-3 font-medium">Run</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Context</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Tokens</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Cost</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {runRows.map((row, index) => (
                    <tr className="align-top" key={rowKey(row, index, ["run_id", "name", "run_name"])}>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1">
                          {rowLinkToRun(row) ? (
                            <Link
                              className="font-medium text-foreground underline-offset-4 hover:text-primary hover:underline"
                              href={rowLinkToRun(row)!}
                            >
                              {rowLabel(row, "run_id", "Run")}
                            </Link>
                          ) : (
                            <p className="font-medium text-foreground">{rowLabel(row, "run_id", "Run")}</p>
                          )}
                          <p className="text-xs text-muted-foreground">
                            {rowLabel(row, "run_type", "Run type")}
                            {readText(row, ["run_state"]) ? ` / ${readText(row, ["run_state"])}` : ""}
                          </p>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1 text-sm">
                          <span className="font-medium text-foreground">{rowText(row, ["agent_name", "agent_names"], "Agent")}</span>
                          <span className="text-muted-foreground">{rowText(row, ["model_name", "model_names"], "Model")}</span>
                          <span className="text-muted-foreground">{rowText(row, ["stage_names"], "No stage context")}</span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <ShareCell
                          maxValue={totalTokens}
                          sharePercent={readNumber(row, ["token_share_percent"]) ?? safeShare(readNumber(row, ["total_tokens"]), totalTokens)}
                          value={formatTokens(readNumber(row, ["total_tokens", "tokens", "token_total"]))}
                        />
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <ShareCell
                          maxValue={totalCost}
                          sharePercent={readNumber(row, ["cost_share_percent"]) ?? safeShare(readNumber(row, ["estimated_cost"]), totalCost)}
                          tone="warning"
                          value={formatCost(readNumber(row, ["estimated_cost", "cost", "total_cost"]))}
                        />
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        {rowLinkToRun(row) ? (
                          <Button asChild size="sm" variant="outline">
                            <Link href={rowLinkToRun(row)!}>Open run</Link>
                          </Button>
                        ) : (
                          <span className="text-xs text-muted-foreground">No drilldown</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.02fr_0.98fr]">
        <article className="rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
          <SectionHeader
            eyebrow="Trend"
            title="Usage trend"
            description="Daily buckets now call out whether usage is stable, elevated, or spiking instead of leaving operators to infer every movement from raw totals alone."
          />

          <div className="grid gap-4 border-b border-border/80 px-6 py-5 md:grid-cols-3">
            <MetricCard
              label="Latest bucket"
              value={latestTrend ? formatTokens(readNumber(latestTrend, ["total_tokens"])) : "n/a"}
            />
            <MetricCard
              label="Latest cost"
              value={latestTrend ? formatCost(readNumber(latestTrend, ["estimated_cost"])) : "n/a"}
            />
            <MetricCard
              label="Latest signal"
              value={latestTrend ? rowSignal(latestTrend) : "n/a"}
            />
          </div>

          {trendRows.length === 0 ? (
            <EmptySection
              title="No trend rows"
              copy="There is no trend data for the current scope. Expand the date range to surface the usage timeline."
            />
          ) : (
            <div className="overflow-x-auto px-6 py-5">
              <table className="min-w-[1080px] table-fixed border-separate border-spacing-0">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                    <th className="border-b border-border px-3 py-3 font-medium">Bucket</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Volume</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Cost</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Records</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Delta</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Signal</th>
                  </tr>
                </thead>
                <tbody>
                  {trendRows.map((row, index) => {
                    const totalTokens = readNumber(row, ["total_tokens", "tokens", "token_total"]);
                    const barWidth = maxTokenVolume > 0 && totalTokens !== null
                      ? Math.max(6, Math.round((totalTokens / maxTokenVolume) * 100))
                      : 0;

                    return (
                      <tr className="align-top" key={rowKey(row, index, ["period", "bucket_date", "date", "bucket_label", "name"])}>
                        <td className="border-b border-border/70 px-3 py-4">
                          <div className="grid gap-1">
                            <p className="font-medium text-foreground">{rowText(row, ["period", "bucket_date"], "Bucket")}</p>
                            <p className="text-xs text-muted-foreground">
                              {formatTimestamp(readText(row, ["interval_start", "bucket_date", "date", "last_seen_at"]))}
                            </p>
                          </div>
                        </td>
                        <td className="border-b border-border/70 px-3 py-4">
                          <div className="grid gap-2">
                            <div className="h-2 rounded-full bg-muted">
                              <div
                                className="h-2 rounded-full bg-primary"
                                style={{ width: barWidth ? `${barWidth}%` : "0%" }}
                              />
                            </div>
                            <p className="text-sm font-medium text-foreground">{formatTokens(totalTokens)}</p>
                          </div>
                        </td>
                        <td className="border-b border-border/70 px-3 py-4 text-sm text-foreground">
                          {formatCost(readNumber(row, ["estimated_cost", "cost", "total_cost"]))}
                        </td>
                        <td className="border-b border-border/70 px-3 py-4">
                          <div className="grid gap-1 text-sm">
                            <span className="font-medium text-foreground">
                              {formatCount(readNumber(row, ["record_count", "usage_record_count", "count"]))} rows
                            </span>
                            <span className="text-muted-foreground">
                              {formatCount(readNumber(row, ["run_count"]))} runs / {formatCount(readNumber(row, ["candidate_count"]))} candidates
                            </span>
                          </div>
                        </td>
                        <td className="border-b border-border/70 px-3 py-4">
                          <div className="grid gap-1 text-sm">
                            <span className="font-medium text-foreground">
                              {formatSignedPercent(readNumber(row, ["token_delta_percent"]))} tokens
                            </span>
                            <span className="text-muted-foreground">
                              {formatSignedPercent(readNumber(row, ["cost_delta_percent"]))} cost
                            </span>
                          </div>
                        </td>
                        <td className="border-b border-border/70 px-3 py-4">
                          <div className="grid gap-2">
                            <span
                              className={cn("inline-flex w-fit rounded-full px-2.5 py-1 text-xs font-medium", trendBadgeClasses(row))}
                            >
                              {rowSignal(row)}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {rowSummary(row, "No trend note stored.")}
                            </span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </article>

        <article className="rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
          <SectionHeader
            eyebrow="Anomalies"
            title="Anomaly drilldown"
            description="Outlier rows now expose enough context to move from a cost signal into review or run diagnosis without leaving the usage dashboard blindly."
          />

          {anomalyRows.length === 0 ? (
            <EmptySection
              title="No anomaly candidates"
              copy="The current scope did not return unusual usage rows. Broaden the date range or clear the filters to inspect drift."
            />
          ) : (
            <div className="overflow-x-auto px-6 py-5">
              <table className="min-w-[1560px] table-fixed border-separate border-spacing-0">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                    <th className="border-b border-border px-3 py-3 font-medium">Signal</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Context</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Observed</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Baseline</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Review context</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Identifiers</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {anomalyRows.map((row, index) => (
                    <tr className="align-top" key={rowKey(row, index, ["signal", "reason", "name", "run_id"])}>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2">
                          <span
                            className={cn("inline-flex w-fit rounded-full px-2.5 py-1 text-xs font-medium", anomalyBadgeClasses(row))}
                          >
                            {rowSignal(row)}
                          </span>
                          <p className="text-sm leading-6 text-foreground">{rowSummary(row, "No anomaly reason stored.")}</p>
                          <p className="text-xs text-muted-foreground">
                            Score {formatCount(readNumber(row, ["anomaly_score"]))} / {readStringArray(row, ["anomaly_reasons"]).join(", ")}
                          </p>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1 text-sm">
                          <span className="font-medium text-foreground">{rowLabel(row, "run_id", "Run")}</span>
                          <span className="text-muted-foreground">
                            {rowText(row, ["agent_name", "agent_names"], "Agent")}
                            {" / "}
                            {rowText(row, ["model_name", "model_names"], "Model")}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {rowText(row, ["product_name"], "No product context")}
                            {readText(row, ["bank_code"]) ? ` / ${readText(row, ["bank_code"])}` : ""}
                            {readText(row, ["product_type"]) ? ` / ${readText(row, ["product_type"])}` : ""}
                          </span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1 text-sm">
                          <span className="font-medium text-foreground">
                            {formatTokens(readNumber(row, ["total_tokens", "observed_total_tokens", "tokens"]))}
                          </span>
                          <span className="text-muted-foreground">
                            {formatCost(readNumber(row, ["estimated_cost", "observed_cost", "cost"]))}
                          </span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1 text-sm">
                          <span className="font-medium text-foreground">
                            {formatTokens(readNumber(row, ["baseline_total_tokens", "expected_total_tokens"]))}
                          </span>
                          <span className="text-muted-foreground">
                            {formatCost(readNumber(row, ["baseline_cost", "expected_cost"]))}
                          </span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1 text-sm">
                          <span className="font-medium text-foreground">
                            {rowText(row, ["review_state"], "No linked review state")}
                          </span>
                          <span className="text-muted-foreground">
                            {rowText(row, ["validation_status"], "No validation context")}
                          </span>
                          <span className="text-muted-foreground">
                            {rowText(row, ["queue_reason_code"], "No queue reason")}
                          </span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1 text-sm">
                          <span className="font-medium text-foreground">{rowText(row, ["llm_usage_id"], "Usage id")}</span>
                          <span className="text-muted-foreground">{rowText(row, ["candidate_id"], "No candidate id")}</span>
                          <span className="text-muted-foreground">{rowText(row, ["model_execution_id"], "No model execution id")}</span>
                          <span className="text-muted-foreground">{rowText(row, ["provider_request_id"], "No provider request id")}</span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="flex flex-col gap-2">
                          {rowLinkToReview(row) ? (
                            <Button asChild size="sm" variant="outline">
                              <Link href={rowLinkToReview(row)!}>Open review</Link>
                            </Button>
                          ) : null}
                          {rowLinkToRun(row) ? (
                            <Button asChild size="sm" variant="outline">
                              <Link href={rowLinkToRun(row)!}>Open run</Link>
                            </Button>
                          ) : null}
                          {!rowLinkToReview(row) && !rowLinkToRun(row) ? (
                            <span className="text-xs text-muted-foreground">No related drilldown</span>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>
      </div>
    </section>
  );
}

function SectionHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return (
    <div className="flex flex-col gap-3 border-b border-border/80 px-6 py-5">
      <div className="max-w-3xl">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{eyebrow}</p>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{title}</h2>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border/80 bg-background px-4 py-4">
      <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
      <p className="mt-2 text-sm font-medium text-foreground">{value}</p>
    </div>
  );
}

function SignalCard({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="rounded-[1.5rem] border border-border/80 bg-background p-4">
      <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
      <p className="mt-2 text-sm font-medium text-foreground">{value}</p>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{note}</p>
    </div>
  );
}

function HotspotCard({
  label,
  value,
  note,
  shareValue,
  actionHref,
  actionLabel,
}: {
  label: string;
  value: string;
  note: string;
  shareValue: number | null;
  actionHref: string;
  actionLabel: string;
}) {
  return (
    <div className="rounded-[1.5rem] border border-border/80 bg-background p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
          <p className="mt-2 text-sm font-medium text-foreground">{value}</p>
        </div>
        <span className="rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
          {formatPercent(shareValue)}
        </span>
      </div>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{note}</p>
      <div className="mt-4">
        {actionHref ? (
          <Button asChild size="sm" variant="outline">
            <Link href={actionHref}>{actionLabel}</Link>
          </Button>
        ) : (
          <span className="text-xs text-muted-foreground">No drilldown</span>
        )}
      </div>
    </div>
  );
}

function ShareCell({
  value,
  sharePercent,
  maxValue,
  tone = "primary",
}: {
  value: string;
  sharePercent: number;
  maxValue: number;
  tone?: "primary" | "warning";
}) {
  const barClass = tone === "warning" ? "bg-warning" : "bg-primary";
  const clampedPercent = Math.max(0, Math.min(100, sharePercent));

  return (
    <div className="grid gap-2">
      <div className="h-2 rounded-full bg-muted">
        <div className={cn("h-2 rounded-full", barClass)} style={{ width: maxValue > 0 ? `${Math.max(6, clampedPercent)}%` : "0%" }} />
      </div>
      <div className="grid gap-1 text-sm">
        <span className="font-medium text-foreground">{value}</span>
        <span className="text-muted-foreground">{formatPercent(sharePercent)}</span>
      </div>
    </div>
  );
}

function EmptySection({ title, copy }: { title: string; copy: string }) {
  return (
    <div className="px-6 py-8">
      <div className="rounded-[1.5rem] border border-dashed border-border bg-background px-6 py-8">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{title}</p>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">{copy}</p>
      </div>
    </div>
  );
}

function buildActiveFilterItems(filters: LlmUsagePageFilters) {
  const items: string[] = [];
  if (filters.search) {
    items.push(`Search ${filters.search}`);
  }
  if (filters.from || filters.to) {
    items.push(`${filters.from || "Start"} to ${filters.to || "Now"}`);
  }
  if (filters.runId) {
    items.push(`Run ${filters.runId}`);
  }
  if (filters.agentName) {
    items.push(`Agent ${filters.agentName}`);
  }
  if (filters.modelName) {
    items.push(`Model ${filters.modelName}`);
  }
  if (filters.providerName) {
    items.push(`Provider ${filters.providerName}`);
  }
  if (filters.stage) {
    items.push(`Stage ${filters.stage}`);
  }
  return items;
}

function buildUsageHref(filters: LlmUsagePageFilters, overrides: Partial<LlmUsagePageFilters>) {
  const next = {
    ...filters,
    ...overrides,
  };
  const params = new URLSearchParams();
  if (next.search) {
    params.set("q", next.search);
  }
  if (next.from) {
    params.set("from", next.from);
  }
  if (next.to) {
    params.set("to", next.to);
  }
  if (next.runId) {
    params.set("run_id", next.runId);
  }
  if (next.agentName) {
    params.set("agent_name", next.agentName);
  }
  if (next.modelName) {
    params.set("model_name", next.modelName);
  }
  if (next.providerName) {
    params.set("provider_name", next.providerName);
  }
  if (next.stage) {
    params.set("stage", next.stage);
  }
  const query = params.toString();
  return query ? `/admin/usage?${query}` : "/admin/usage";
}

function topUsageRow(rows: UsageRow[]) {
  return [...rows].sort((left, right) => {
    const leftCost = readNumber(left, ["estimated_cost", "cost", "total_cost"]) ?? 0;
    const rightCost = readNumber(right, ["estimated_cost", "cost", "total_cost"]) ?? 0;
    if (rightCost !== leftCost) {
      return rightCost - leftCost;
    }
    const leftTokens = readNumber(left, ["total_tokens", "tokens", "token_total"]) ?? 0;
    const rightTokens = readNumber(right, ["total_tokens", "tokens", "token_total"]) ?? 0;
    return rightTokens - leftTokens;
  })[0];
}

function readNumber(row: Record<string, unknown>, keys: string[]) {
  for (const key of keys) {
    const value = row[key];
    if (typeof value === "number" && Number.isFinite(value)) {
      return value;
    }
    if (typeof value === "string" && value.trim()) {
      const parsed = Number(value);
      if (Number.isFinite(parsed)) {
        return parsed;
      }
    }
  }
  return null;
}

function readText(row: Record<string, unknown>, keys: string[]) {
  for (const key of keys) {
    const value = row[key];
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return "";
}

function rowLabel(row: Record<string, unknown>, key: string, fallback: string) {
  const value = row[key];
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  return fallback;
}

function rowText(row: Record<string, unknown>, keys: string[], fallback: string) {
  const text = readText(row, keys);
  if (text) {
    return text;
  }
  const values = readStringArray(row, keys);
  return values.length ? values.join(", ") : fallback;
}

function rowSummary(row: Record<string, unknown>, fallback: string) {
  return (
    readText(row, ["reason", "summary", "note", "message", "signal_reason"]) ||
    readStringArray(row, ["anomaly_reasons"]).join(", ") ||
    fallback
  );
}

function rowSignal(row: Record<string, unknown>) {
  return readText(row, ["signal", "severity", "trend_state", "anomaly_type", "reason_code"]) || "Signal";
}

function rowLinkToRun(row: UsageRow) {
  const runId = readText(row, ["run_id"]);
  return runId ? `/admin/runs/${runId}` : "";
}

function rowLinkToReview(row: UsageRow) {
  const reviewTaskId = readText(row, ["review_task_id"]);
  return reviewTaskId ? `/admin/reviews/${reviewTaskId}` : "";
}

function rowKey(row: UsageRow, index: number, keys: string[]) {
  const candidate = keys.map((key) => readText(row, [key])).find(Boolean);
  return candidate || String(index);
}

function readStringArray(row: UsageRow, keys: string[]) {
  for (const key of keys) {
    const value = row[key];
    if (!Array.isArray(value)) {
      continue;
    }
    const items = value
      .map((item) => (typeof item === "string" ? item.trim() : ""))
      .filter(Boolean);
    if (items.length) {
      return items;
    }
  }
  return [] as string[];
}

function trendBadgeClasses(row: UsageRow) {
  const value = readText(row, ["trend_state", "signal", "severity", "status"]);
  if (value === "critical" || value === "high" || value === "spike") {
    return "bg-destructive/10 text-destructive";
  }
  if (value === "warning" || value === "elevated") {
    return "bg-warning-soft text-warning";
  }
  if (value === "stable" || value === "normal" || value === "baseline") {
    return "bg-success-soft text-success";
  }
  return "bg-muted text-muted-foreground";
}

function anomalyBadgeClasses(row: UsageRow) {
  const value = readText(row, ["signal", "severity", "anomaly_type", "status"]);
  if (value === "critical" || value === "high" || value === "spike") {
    return "bg-destructive/10 text-destructive";
  }
  if (value === "warning" || value === "elevated" || value === "medium") {
    return "bg-warning-soft text-warning";
  }
  if (value === "low" || value === "info") {
    return "bg-info-soft text-info";
  }
  return "bg-muted text-muted-foreground";
}

function formatCount(value: number | null, fallback?: number) {
  const nextValue = value ?? fallback ?? 0;
  return nextValue.toLocaleString("en-CA");
}

function formatTokens(value: number | null) {
  if (value === null) {
    return "n/a";
  }
  return value.toLocaleString("en-CA", {
    maximumFractionDigits: value % 1 === 0 ? 0 : 2,
  });
}

function formatCost(value: number | null) {
  if (value === null) {
    return "n/a";
  }
  return `$${value.toFixed(6)}`;
}

function formatPercent(value: number | null) {
  if (value === null) {
    return "n/a";
  }
  return `${value.toFixed(2)}%`;
}

function formatSignedPercent(value: number | null) {
  if (value === null) {
    return "n/a";
  }
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function formatTimestamp(value: string) {
  if (!value) {
    return "n/a";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("en-CA", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsed);
}

function formatCoverage(start: string, end: string) {
  if (!start && !end) {
    return "No recorded window";
  }
  return `${formatTimestamp(start)} -> ${formatTimestamp(end)}`;
}

function maxTokens(...rows: UsageRow[][]) {
  let max = 0;
  for (const rowGroup of rows) {
    for (const row of rowGroup) {
      const value = readNumber(row, ["total_tokens", "tokens", "token_total"]);
      if (value !== null && value > max) {
        max = value;
      }
    }
  }
  return max;
}

function safeShare(value: number | null, total: number) {
  if (value === null || total <= 0) {
    return 0;
  }
  return Number(((value / total) * 100).toFixed(2));
}
