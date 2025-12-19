"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { ValueType } from "recharts/types/component/DefaultTooltipContent";

export type Row = { date: string; value: number };

type Props = { data: Row[] };

export default function TrendChart({ data }: Props) {
  if (!data || data.length === 0) {
    return <div style={{ color: "#6b7280" }}>No trend data</div>;
  }

  const values = data.map((d) => d.value).filter((x) => Number.isFinite(x));
  const min = Math.min(...values);
  const max = Math.max(...values);

  const PAD_RATIO = 0.12;

  const yMin = min * (1 - PAD_RATIO);
  const yMax = max * (1 + PAD_RATIO);

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart
        data={data}
        margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis
          domain={[yMin, yMax]}
          tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
        />
        <Tooltip
          formatter={(value: ValueType) => {
            const n = typeof value === "number" ? value : Number(value);
            if (!Number.isFinite(n)) return "—";
            return `$${n.toLocaleString("en-US", {
              maximumFractionDigits: 0,
            })}`;
          }}
        />
        <Line
          type="monotone"
          dataKey="value"
          stroke="#2563eb"
          strokeWidth={3}
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
