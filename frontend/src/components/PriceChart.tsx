/**
 * Historical price chart using Recharts.
 * Shows 24K, 22K, and 18K lines over the fetched history window.
 */

import { format } from "date-fns";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { GoldPrice } from "../lib/api";

interface PriceChartProps {
  data: GoldPrice[];
}

function formatK(value: number): string {
  return (value / 1000).toFixed(1) + "K";
}

export default function PriceChart({ data }: PriceChartProps) {
  // Recharts expects data in chronological order (oldest → newest)
  const chartData = [...data]
    .reverse()
    .map((p) => ({
      date: format(new Date(p.fetched_at), "MMM d"),
      "24K": p.price_24k ? +p.price_24k.toFixed(2) : null,
      "22K": p.price_22k ? +p.price_22k.toFixed(2) : null,
      "18K": p.price_18k ? +p.price_18k.toFixed(2) : null,
    }));

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-500 text-sm">
        No historical data yet. Prices will appear here after the first fetch.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis
          dataKey="date"
          tick={{ fill: "#9ca3af", fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: "#374151" }}
        />
        <YAxis
          tickFormatter={formatK}
          tick={{ fill: "#9ca3af", fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: "#374151" }}
          width={48}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#111827",
            border: "1px solid #374151",
            borderRadius: "8px",
            color: "#f3f4f6",
            fontSize: "13px",
          }}
          formatter={(value: number) =>
            [`${value.toLocaleString("en-US", { minimumFractionDigits: 2 })} ETB/g`]
          }
        />
        <Legend
          wrapperStyle={{ fontSize: "12px", color: "#9ca3af", paddingTop: "12px" }}
        />
        <Line
          type="monotone"
          dataKey="24K"
          stroke="#f59e0b"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
        />
        <Line
          type="monotone"
          dataKey="22K"
          stroke="#60a5fa"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
        />
        <Line
          type="monotone"
          dataKey="18K"
          stroke="#a78bfa"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
