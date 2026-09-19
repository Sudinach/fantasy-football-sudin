"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export interface TrendPoint {
  event: number;
  points: number;
  overall_rank: number;
}

function ChartTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: TrendPoint }[];
}) {
  if (!active || !payload || payload.length === 0) return null;
  const point = payload[0].payload;
  return (
    <div className="rounded border border-zinc-200 bg-white px-3 py-2 text-xs shadow-sm dark:border-zinc-700 dark:bg-zinc-900">
      <p className="font-medium">Gameweek {point.event}</p>
      <p className="text-zinc-600 dark:text-zinc-300">{point.points} points</p>
      <p className="text-zinc-500 dark:text-zinc-400">
        Rank {point.overall_rank.toLocaleString("en-GB")}
      </p>
    </div>
  );
}

export default function PointsTrendChart({ data }: { data: TrendPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: -16 }}>
        <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
        <XAxis
          dataKey="event"
          tickFormatter={(v: number) => `GW${v}`}
          tick={{ fontSize: 12, fill: "var(--chart-grid)" }}
          axisLine={{ stroke: "var(--chart-grid)" }}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 12, fill: "var(--chart-grid)" }}
          axisLine={false}
          tickLine={false}
          width={32}
        />
        <Tooltip content={<ChartTooltip />} />
        <Line
          type="monotone"
          dataKey="points"
          stroke="var(--chart-line)"
          strokeWidth={2}
          dot={{ r: 4, fill: "var(--chart-line)", strokeWidth: 0 }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
