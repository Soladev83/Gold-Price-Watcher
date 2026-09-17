/**
 * Displays the data source label + disclaimer — always visible per the spec requirement
 * to keep source, timestamp, and methodology visible in every view.
 */

import { Info } from "lucide-react";
import { format } from "date-fns";

interface SourceBadgeProps {
  sourceLabel: string;
  sourceUrl: string;
  fetchedAt: string;
}

export default function SourceBadge({ sourceLabel, sourceUrl, fetchedAt }: SourceBadgeProps) {
  return (
    <div className="flex items-start gap-2 rounded-xl bg-gray-800/40 border border-gray-700/40 px-4 py-3">
      <Info className="w-4 h-4 text-gray-500 mt-0.5 flex-shrink-0" />
      <div className="flex flex-col gap-0.5">
        <p className="text-xs text-gray-400">
          {sourceLabel}
        </p>
        <p className="text-xs text-gray-600">
          Last fetched:{" "}
          {format(new Date(fetchedAt), "PPpp")} UTC ·{" "}
          <a
            href={sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-gold-600 hover:text-gold-400 underline underline-offset-2"
          >
            View source
          </a>
        </p>
      </div>
    </div>
  );
}
