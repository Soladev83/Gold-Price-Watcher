/**
 * Alert rules management panel.
 * Lists existing rules and provides a form to create new ones.
 */

import { Bell, BellOff, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { AlertRule, AlertRulePayload } from "../lib/api";

interface AlertRulesPanelProps {
  rules: AlertRule[];
  loading: boolean;
  onCreate: (payload: AlertRulePayload) => Promise<void>;
  onToggle: (id: number, is_active: boolean) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
}

const RULE_TYPE_LABELS: Record<string, string> = {
  above: "Price rises above",
  below: "Price drops below",
  pct_change: "Price changes by ≥",
};

const PURITY_OPTIONS = ["24K", "22K", "18K"] as const;

export default function AlertRulesPanel({
  rules,
  loading,
  onCreate,
  onToggle,
  onDelete,
}: AlertRulesPanelProps) {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<AlertRulePayload>({
    rule_type: "above",
    threshold: 0,
    purity: "24K",
    label: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.threshold || form.threshold <= 0) {
      setFormError("Threshold must be greater than 0.");
      return;
    }
    setSubmitting(true);
    setFormError(null);
    try {
      await onCreate({
        ...form,
        label: form.label?.trim() || undefined,
      });
      setShowForm(false);
      setForm({ rule_type: "above", threshold: 0, purity: "24K", label: "" });
    } catch {
      setFormError("Failed to create alert rule. Check the backend.");
    } finally {
      setSubmitting(false);
    }
  };

  const thresholdSuffix = form.rule_type === "pct_change" ? "%" : "ETB/g";

  return (
    <div className="rounded-2xl bg-gray-800/60 border border-gray-700/50 p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-100 flex items-center gap-2">
          <Bell className="w-4 h-4 text-gold-400" />
          Alert Rules
        </h2>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="flex items-center gap-1 text-xs font-medium bg-gold-600 hover:bg-gold-500 text-white px-3 py-1.5 rounded-lg transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          New Rule
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="bg-gray-900/60 rounded-xl p-4 flex flex-col gap-3 border border-gray-700"
        >
          <div className="grid grid-cols-2 gap-3">
            {/* Rule type */}
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-400">Rule type</label>
              <select
                value={form.rule_type}
                onChange={(e) =>
                  setForm((f) => ({ ...f, rule_type: e.target.value as AlertRulePayload["rule_type"] }))
                }
                className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-gold-500"
              >
                <option value="above">Price rises above</option>
                <option value="below">Price drops below</option>
                <option value="pct_change">% change ≥</option>
              </select>
            </div>

            {/* Purity */}
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-400">Purity</label>
              <select
                value={form.purity}
                onChange={(e) =>
                  setForm((f) => ({ ...f, purity: e.target.value as AlertRulePayload["purity"] }))
                }
                className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-gold-500"
              >
                {PURITY_OPTIONS.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>

            {/* Threshold */}
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-400">Threshold ({thresholdSuffix})</label>
              <input
                type="number"
                min={0}
                step={form.rule_type === "pct_change" ? "0.1" : "1"}
                value={form.threshold || ""}
                onChange={(e) => setForm((f) => ({ ...f, threshold: parseFloat(e.target.value) || 0 }))}
                placeholder={form.rule_type === "pct_change" ? "e.g. 3.5" : "e.g. 25000"}
                className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-gold-500"
              />
            </div>

            {/* Label */}
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-400">Label (optional)</label>
              <input
                type="text"
                value={form.label || ""}
                onChange={(e) => setForm((f) => ({ ...f, label: e.target.value }))}
                placeholder="e.g. Sell signal"
                maxLength={200}
                className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-gold-500"
              />
            </div>
          </div>

          {formError && <p className="text-xs text-red-400">{formError}</p>}

          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="text-xs text-gray-400 hover:text-gray-200 px-3 py-1.5"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="text-xs font-medium bg-gold-600 hover:bg-gold-500 disabled:opacity-50 text-white px-4 py-1.5 rounded-lg transition-colors"
            >
              {submitting ? "Saving…" : "Create Rule"}
            </button>
          </div>
        </form>
      )}

      {/* Rules list */}
      {loading ? (
        <p className="text-sm text-gray-500">Loading rules…</p>
      ) : rules.length === 0 ? (
        <p className="text-sm text-gray-500">No alert rules yet. Create one above.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {rules.map((rule) => (
            <li
              key={rule.id}
              className={`flex items-center justify-between rounded-xl px-4 py-3 border transition-opacity ${
                rule.is_active
                  ? "bg-gray-900/50 border-gray-700"
                  : "bg-gray-900/20 border-gray-800 opacity-50"
              }`}
            >
              <div className="flex flex-col gap-0.5">
                <span className="text-sm text-gray-200">
                  <span className="text-gold-400 font-medium">{rule.purity}</span>{" "}
                  {RULE_TYPE_LABELS[rule.rule_type]}{" "}
                  <span className="font-semibold text-gray-100">
                    {rule.threshold.toLocaleString("en-US")}
                    {rule.rule_type === "pct_change" ? "%" : " ETB/g"}
                  </span>
                </span>
                {rule.label && (
                  <span className="text-xs text-gray-500">{rule.label}</span>
                )}
                {rule.last_triggered_at && (
                  <span className="text-xs text-gray-600">
                    Last fired:{" "}
                    {new Date(rule.last_triggered_at).toLocaleString("en-US", {
                      dateStyle: "medium",
                      timeStyle: "short",
                    })}
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => onToggle(rule.id, !rule.is_active)}
                  title={rule.is_active ? "Disable rule" : "Enable rule"}
                  className="text-gray-500 hover:text-gold-400 transition-colors"
                >
                  {rule.is_active ? (
                    <Bell className="w-4 h-4" />
                  ) : (
                    <BellOff className="w-4 h-4" />
                  )}
                </button>
                <button
                  onClick={() => onDelete(rule.id)}
                  title="Delete rule"
                  className="text-gray-600 hover:text-red-400 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
