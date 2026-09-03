import type { PublicDashboardScatterResponse } from "@/lib/public-api";

const CHART_WIDTH = 720;
const CHART_HEIGHT = 320;
const PLOT_LEFT = 72;
const PLOT_RIGHT = 24;
const PLOT_TOP = 20;
const PLOT_BOTTOM = 54;
const TICK_COUNT = 5;

export function PublicScatterChart({
  scatter
}: {
  scatter: PublicDashboardScatterResponse;
}) {
  const xAxis = scatter.x_axis;
  const yAxis = scatter.y_axis;
  if (!scatter.points.length || !xAxis || !yAxis) {
    return null;
  }

  const xValues = scatter.points.map((point) => point.x_value);
  const yValues = scatter.points.map((point) => point.y_value);
  const xDomain = createDomain(xValues);
  const yDomain = createDomain(yValues);
  const plotWidth = CHART_WIDTH - PLOT_LEFT - PLOT_RIGHT;
  const plotHeight = CHART_HEIGHT - PLOT_TOP - PLOT_BOTTOM;
  const chartLabel = `${scatter.title ?? "Product comparison"}. ${xAxis.label} by ${yAxis.label}. ${scatter.points.length} products.`;

  return (
    <div className="w-full overflow-hidden">
      <svg
        aria-labelledby="public-scatter-chart-title"
        className="h-72 w-full text-muted-foreground"
        preserveAspectRatio="xMidYMid meet"
        role="img"
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
      >
        <title id="public-scatter-chart-title">{chartLabel}</title>
        {createTicks(yDomain).map((tick) => {
          const y = scaleY(tick, yDomain, plotHeight);
          return (
            <g key={`y-${tick}`}>
              <line
                className="stroke-border"
                x1={PLOT_LEFT}
                x2={CHART_WIDTH - PLOT_RIGHT}
                y1={y}
                y2={y}
              />
              <text className="fill-muted-foreground text-[11px]" textAnchor="end" x={PLOT_LEFT - 10} y={y + 4}>
                {formatAxisValue(tick, yAxis.unit)}
              </text>
            </g>
          );
        })}
        {createTicks(xDomain).map((tick) => {
          const x = scaleX(tick, xDomain, plotWidth);
          return (
            <g key={`x-${tick}`}>
              <line
                className="stroke-border/70"
                x1={x}
                x2={x}
                y1={PLOT_TOP}
                y2={CHART_HEIGHT - PLOT_BOTTOM}
              />
              <text
                className="fill-muted-foreground text-[11px]"
                textAnchor="middle"
                x={x}
                y={CHART_HEIGHT - PLOT_BOTTOM + 20}
              >
                {formatAxisValue(tick, xAxis.unit)}
              </text>
            </g>
          );
        })}
        <line
          className="stroke-foreground/40"
          x1={PLOT_LEFT}
          x2={CHART_WIDTH - PLOT_RIGHT}
          y1={CHART_HEIGHT - PLOT_BOTTOM}
          y2={CHART_HEIGHT - PLOT_BOTTOM}
        />
        <line
          className="stroke-foreground/40"
          x1={PLOT_LEFT}
          x2={PLOT_LEFT}
          y1={PLOT_TOP}
          y2={CHART_HEIGHT - PLOT_BOTTOM}
        />
        {scatter.points.map((point) => (
          <circle
            className="fill-primary stroke-card"
            cx={scaleX(point.x_value, xDomain, plotWidth)}
            cy={scaleY(point.y_value, yDomain, plotHeight)}
            key={point.product_id}
            r={point.highlight_badge_code ? 7 : 5}
            strokeWidth={2}
          >
            <title>
              {`${point.product_name} - ${point.bank_name}. ${xAxis.label}: ${formatAxisValue(point.x_value, xAxis.unit)}. ${yAxis.label}: ${formatAxisValue(point.y_value, yAxis.unit)}.`}
            </title>
          </circle>
        ))}
        <text
          className="fill-foreground text-xs font-medium"
          textAnchor="middle"
          x={PLOT_LEFT + plotWidth / 2}
          y={CHART_HEIGHT - 8}
        >
          {xAxis.label}
        </text>
        <text
          className="fill-foreground text-xs font-medium"
          textAnchor="middle"
          transform={`rotate(-90 16 ${PLOT_TOP + plotHeight / 2})`}
          x={16}
          y={PLOT_TOP + plotHeight / 2}
        >
          {yAxis.label}
        </text>
      </svg>
      <table className="sr-only">
        <caption>{chartLabel}</caption>
        <thead>
          <tr>
            <th>Product</th>
            <th>Bank</th>
            <th>{xAxis.label}</th>
            <th>{yAxis.label}</th>
          </tr>
        </thead>
        <tbody>
          {scatter.points.map((point) => (
            <tr key={point.product_id}>
              <td>{point.product_name}</td>
              <td>{point.bank_name}</td>
              <td>{formatAxisValue(point.x_value, xAxis.unit)}</td>
              <td>{formatAxisValue(point.y_value, yAxis.unit)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function createDomain(values: number[]): [number, number] {
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  if (minimum === maximum) {
    const padding = Math.max(Math.abs(minimum) * 0.1, 1);
    return [minimum - padding, maximum + padding];
  }
  const padding = (maximum - minimum) * 0.08;
  return [minimum - padding, maximum + padding];
}

function createTicks([minimum, maximum]: [number, number]) {
  const step = (maximum - minimum) / (TICK_COUNT - 1);
  return Array.from({ length: TICK_COUNT }, (_, index) => minimum + step * index);
}

function scaleX(value: number, [minimum, maximum]: [number, number], plotWidth: number) {
  return PLOT_LEFT + ((value - minimum) / (maximum - minimum)) * plotWidth;
}

function scaleY(value: number, [minimum, maximum]: [number, number], plotHeight: number) {
  return PLOT_TOP + plotHeight - ((value - minimum) / (maximum - minimum)) * plotHeight;
}

function formatAxisValue(value: number, unit: string) {
  if (!Number.isFinite(value)) {
    return "Unavailable";
  }
  if (unit === "percent") {
    return `${value.toFixed(2).replace(/\.?0+$/, "")}%`;
  }
  if (unit === "currency") {
    return `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
  }
  if (unit === "days") {
    return `${Math.round(value)}d`;
  }
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}
