/**
 * Main dashboard — live prices, chart, alert rules.
 * Requires authentication.
 */

import { format } from "date-fns";
import { useAuth } from "../lib/auth";
import { useAlertRules, useLatestPrice, usePriceHistory } from "../hooks/useGoldData";
import AlertRulesPanel from "../components/AlertRulesPanel";
import PriceCard from "../components/PriceCard";
import PriceChart from "../components/PriceChart";
import SourceBadge from "../components/SourceBadge";

export default function Dashboard() {
  const { user } = useAuth();
  const { data: latest, loading: latestLoading, error: latestError, reload: reloadLatest } =
    useLatestPrice();
  const { data: history, loading: histLoading, reload: reloadHistory } = usePriceHistory(60);
  const { data: rules, loading: rulesLoading, create, toggle, remove } = useAlertRules();

  const reload = () => {
    reloadLatest();
    reloadHistory();
  };

  const greeting = user?.full_name
    ? `Welcome, ${user.full_name.split(" ")[0]}`
    : "Gold Prices";

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 flex flex-col gap-6">

      {/* Heading */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">{greeting}</h1>
          <p className="text-sm text-gray-500 mt-1">
            {latest
              ? `Updated ${format(new Date(latest.fetched_at), "PPp")} UTC`
              : "Loading latest prices…"}
          </p>
        </div>

        {/* Telegram connection nudge */}
        {user && !user.telegram_chat_id && (
          <a
            href="/settings"
            className="text-xs bg-gold-900/40 border border-gold-700/40 text-gold-400 hover:text-gold-300 px-3 py-1.5 rounded-lg transition-colors hidden sm:block"
          >
            Connect Telegram →
          </a>
        )}
      </div>

      {/* Error state */}
      {latestError && (
        <div className="rounded-xl bg-red-900/30 border border-red-700/40 px-4 py-3 text-sm text-red-300">
          {latestError} — the backend may still be starting up.
        </div>
      )}

      {/* Price cards */}
      {latestLoading && !latest ? (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="rounded-2xl bg-gray-800/40 border border-gray-700/40 h-28 animate-pulse"
            />
          ))}
        </div>
      ) : latest ? (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <PriceCard
            purity="24K"
            price={latest.price_24k}
            changePct={latest.change_24k_pct}
            changeAbs={latest.change_24k_abs}
            highlight
          />
          <PriceCard purity="22K" price={latest.price_22k} />
          <PriceCard purity="18K" price={latest.price_18k} />
        </div>
      ) : null}

      {/* Chart */}
      <div className="rounded-2xl bg-gray-800/60 border border-gray-700/50 p-5">
        <h2 className="text-base font-semibold text-gray-100 mb-4">Price History</h2>
        {histLoading && history.length === 0 ? (
          <div className="h-56 bg-gray-800/40 rounded-xl animate-pulse" />
        ) : (
          <PriceChart data={history} />
        )}
      </div>

      {/* Alert rules — only shown to logged-in users */}
      {user && (
        <AlertRulesPanel
          rules={rules}
          loading={rulesLoading}
          onCreate={async (payload) => { await create(payload); }}
          onToggle={toggle}
          onDelete={remove}
        />
      )}

      {/* Source badge — always visible */}
      {latest && (
        <SourceBadge
          sourceLabel={latest.source_label}
          sourceUrl={latest.source_url}
          fetchedAt={latest.fetched_at}
        />
      )}
    </div>
  );
}
