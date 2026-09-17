/**
 * Displays a single purity price (24K / 22K / 18K) as a stat card.
 */

import { TrendingDown, TrendingUp } from "lucide-react";

interface PriceCardProps {
  purity: string;
  price: number | null;
  changePct?: number | null;
  changeAbs?: number | null;
  highlight?: boolean;
}

function fmt(n: number | null): string {
  if (n === null || n === undefined) return "—";
  return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function PriceCard({
  purity,
  price,
  changePct,
  changeAbs,
  highlight = false,
}: PriceCardProps) {
  const isUp = changeAbs !== null && changeAbs !== undefined && changeAbs > 0;
  const isDown = changeAbs !== null && changeAbs !== undefined && changeAbs < 0;

  return (
    <div
      className={`rounded-2xl p-5 flex flex-col gap-2 border ${
        highlight
          ? "bg-gold-900/30 border-gold-500/40 shadow-lg shadow-gold-900/20"
          : "bg-gray-800/60 border-gray-700/50"
      }`}
    >
      <div className="flex items-center justify-between">
        <span
          className={`text-sm font-semibold tracking-widest uppercase ${
            highlight ? "text-gold-400" : "text-gray-400"
          }`}
        >
          {purity}
        </span>
        {isUp && <TrendingUp className="w-4 h-4 text-emerald-400" />}
        {isDown && <TrendingDown className="w-4 h-4 text-red-400" />}
      </div>

      <div className={`text-2xl font-bold ${highlight ? "text-gold-300" : "text-gray-100"}`}>
        {fmt(price)}
        <span className="text-sm font-normal text-gray-400 ml-1">ETB/g</span>
      </div>

      {changePct !== null && changePct !== undefined && (
        <div
          className={`text-sm font-medium ${
            isUp ? "text-emerald-400" : isDown ? "text-red-400" : "text-gray-400"
          }`}
        >
          {isUp ? "+" : ""}
          {fmt(changeAbs)} ETB ({isUp ? "+" : ""}
          {changePct?.toFixed(2)}%)
        </div>
      )}

      {changePct === null ||
        (changePct === undefined && (
          <div className="text-xs text-gray-500">First record</div>
        ))}
    </div>
  );
}
