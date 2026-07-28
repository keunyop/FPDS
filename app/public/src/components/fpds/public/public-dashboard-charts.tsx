"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis
} from "recharts";

import { type ChartConfig, ChartContainer } from "@/components/ui/chart";
import type { PublicDashboardBreakdownItem, PublicDashboardScatterResponse } from "@/lib/public-api";

type CompositionItem = PublicDashboardBreakdownItem & {
  key: string;
  label: string;
};

const compositionConfig = {
  count: {
    label: "Products",
    color: "var(--chart-1)"
  }
} satisfies ChartConfig;

const typeConfig = {
  count: {
    label: "Products",
    color: "var(--chart-2)"
  }
} satisfies ChartConfig;

const scatterConfig = {
  products: {
    label: "Products",
    color: "var(--chart-1)"
  }
} satisfies ChartConfig;

export function CompositionBarChart({ items }: { items: CompositionItem[] }) {
  const data = items.map((item) => ({
    ...item,
    shortLabel: item.label.length > 12 ? `${item.label.slice(0, 12)}...` : item.label
  }));

  return (
    <ChartContainer className="h-64 w-full" config={compositionConfig}>
      <BarChart data={data} margin={{ bottom: 8, left: 4, right: 8, top: 8 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis axisLine={false} dataKey="shortLabel" interval={0} tick={{ fontSize: 11 }} tickLine={false} />
        <YAxis allowDecimals={false} axisLine={false} tick={{ fontSize: 11 }} tickLine={false} width={32} />
        <Tooltip cursor={{ fill: "rgba(48, 86, 211, 0.08)" }} />
        <Bar dataKey="count" fill="var(--color-count)" radius={[6, 6, 0, 0]} />
      </BarChart>
    </ChartContainer>
  );
}

export function ProductTypeBarChart({ items }: { items: CompositionItem[] }) {
  return (
    <ChartContainer className="h-64 w-full" config={typeConfig}>
      <BarChart data={items} layout="vertical" margin={{ bottom: 8, left: 8, right: 16, top: 8 }}>
        <CartesianGrid horizontal={false} strokeDasharray="3 3" />
        <XAxis allowDecimals={false} axisLine={false} tick={{ fontSize: 11 }} tickLine={false} type="number" />
        <YAxis axisLine={false} dataKey="label" tick={{ fontSize: 11 }} tickLine={false} type="category" width={88} />
        <Tooltip cursor={{ fill: "rgba(15, 118, 110, 0.08)" }} />
        <Bar dataKey="count" fill="var(--color-count)" radius={[0, 6, 6, 0]} />
      </BarChart>
    </ChartContainer>
  );
}

export function PublicScatterChart({ scatter }: { scatter: PublicDashboardScatterResponse }) {
  if (!scatter.points.length || !scatter.x_axis || !scatter.y_axis) {
    return null;
  }

  const data = scatter.points.map((point) => ({
    ...point,
    z: point.highlight_badge_code ? 95 : 70
  }));

  const chartLabel = `${scatter.title ?? "Product comparison"}. ${scatter.x_axis.label} by ${scatter.y_axis.label}. ${data.length} products.`;

  return (
    <div>
    <ChartContainer aria-label={chartLabel} className="h-72 w-full" config={scatterConfig} role="img">
      <ScatterChart margin={{ bottom: 16, left: 4, right: 16, top: 12 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          axisLine={false}
          dataKey="x_value"
          name={scatter.x_axis.label}
          tick={{ fontSize: 11 }}
          tickFormatter={(value) => formatAxisValue(Number(value), scatter.x_axis?.unit ?? "")}
          tickLine={false}
          type="number"
        />
        <YAxis
          axisLine={false}
          dataKey="y_value"
          name={scatter.y_axis.label}
          tick={{ fontSize: 11 }}
          tickFormatter={(value) => formatAxisValue(Number(value), scatter.y_axis?.unit ?? "")}
          tickLine={false}
          type="number"
          width={42}
        />
        <ZAxis dataKey="z" range={[60, 110]} />
        <Tooltip
          cursor={{ strokeDasharray: "3 3" }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) {
              return null;
            }
            const point = payload[0]?.payload as (typeof data)[number] | undefined;
            if (!point) {
              return null;
            }
            return (
              <div className="rounded-lg border border-border bg-card px-3 py-2 text-xs shadow-lg">
                <p className="font-medium text-foreground">{point.product_name}</p>
                <p className="mt-1 text-muted-foreground">{point.bank_name}</p>
                <p className="mt-2 tabular-nums text-foreground">
                  {scatter.x_axis?.label}: {formatAxisValue(point.x_value, scatter.x_axis?.unit ?? "")}
                </p>
                <p className="tabular-nums text-foreground">
                  {scatter.y_axis?.label}: {formatAxisValue(point.y_value, scatter.y_axis?.unit ?? "")}
                </p>
              </div>
            );
          }}
        />
        <Scatter data={data} dataKey="y_value" fill="var(--color-products)" name="products" />
      </ScatterChart>
    </ChartContainer>
      <table className="sr-only">
        <caption>{chartLabel}</caption>
        <thead>
          <tr>
            <th>Product</th>
            <th>Bank</th>
            <th>{scatter.x_axis.label}</th>
            <th>{scatter.y_axis.label}</th>
          </tr>
        </thead>
        <tbody>
          {data.map((point) => (
            <tr key={point.product_id}>
              <td>{point.product_name}</td>
              <td>{point.bank_name}</td>
              <td>{formatAxisValue(point.x_value, scatter.x_axis?.unit ?? "")}</td>
              <td>{formatAxisValue(point.y_value, scatter.y_axis?.unit ?? "")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatAxisValue(value: number, unit: string) {
  if (!Number.isFinite(value)) {
    return "—";
  }
  if (unit === "percent") {
    return `${value.toFixed(2).replace(/\.?0+$/, "")}%`;
  }
  if (unit === "currency") {
    return `$${new Intl.NumberFormat("en-CA", { maximumFractionDigits: 0 }).format(value)}`;
  }
  return new Intl.NumberFormat("en-CA", { maximumFractionDigits: 2 }).format(value);
}
