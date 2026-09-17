/**
 * Custom hooks for gold price data — simple fetch + state pattern,
 * no external state management library needed at this scale.
 */

import { useCallback, useEffect, useState } from "react";
import {
  AlertRule,
  AlertRulePayload,
  GoldPrice,
  createAlertRule,
  deleteAlertRule,
  fetchAlertRules,
  fetchLatestPrice,
  fetchPriceHistory,
  triggerManualFetch,
  updateAlertRule,
} from "../lib/api";

// ---------------------------------------------------------------------------
// Latest price + auto-refresh
// ---------------------------------------------------------------------------

export function useLatestPrice(refreshMs = 300_000 /* 5 min */) {
  const [data, setData] = useState<GoldPrice | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const result = await fetchLatestPrice();
      setData(result);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load latest price.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, refreshMs);
    return () => clearInterval(interval);
  }, [load, refreshMs]);

  return { data, loading, error, reload: load };
}

// ---------------------------------------------------------------------------
// Price history
// ---------------------------------------------------------------------------

export function usePriceHistory(limit = 60) {
  const [data, setData] = useState<GoldPrice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const result = await fetchPriceHistory(limit);
      setData(result);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load price history.");
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    load();
  }, [load]);

  return { data, loading, error, reload: load };
}

// ---------------------------------------------------------------------------
// Manual fetch trigger
// ---------------------------------------------------------------------------

export function useManualFetch() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const trigger = useCallback(async () => {
    setLoading(true);
    setMessage(null);
    try {
      const result = await triggerManualFetch();
      setMessage(result.message);
      return result;
    } catch {
      setMessage("Fetch failed. Check backend connectivity.");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { trigger, loading, message };
}

// ---------------------------------------------------------------------------
// Alert rules CRUD
// ---------------------------------------------------------------------------

export function useAlertRules() {
  const [data, setData] = useState<AlertRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const result = await fetchAlertRules();
      setData(result);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load alert rules.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const create = useCallback(
    async (payload: AlertRulePayload) => {
      const rule = await createAlertRule(payload);
      setData((prev) => [rule, ...prev]);
      return rule;
    },
    []
  );

  const toggle = useCallback(async (id: number, is_active: boolean) => {
    const updated = await updateAlertRule(id, { is_active });
    setData((prev) => prev.map((r) => (r.id === id ? updated : r)));
  }, []);

  const remove = useCallback(async (id: number) => {
    await deleteAlertRule(id);
    setData((prev) => prev.filter((r) => r.id !== id));
  }, []);

  return { data, loading, error, reload: load, create, toggle, remove };
}
