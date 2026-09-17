/**
 * Settings page — connect/disconnect Telegram, adjust notification interval.
 */

import { CheckCircle, ExternalLink, Send, Unlink } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth } from "../lib/auth";
import { getTelegramLink, unlinkTelegram, updateMe } from "../lib/api";

export default function Settings() {
  const { user, refreshUser } = useAuth();

  // Telegram connect
  const [telegramLink, setTelegramLink] = useState<string | null>(null);
  const [linkLoading, setLinkLoading] = useState(false);
  const [unlinkLoading, setUnlinkLoading] = useState(false);

  // Notification interval
  const [interval, setInterval_] = useState(user?.notify_interval_hours ?? 48);
  const [intervalSaving, setIntervalSaving] = useState(false);
  const [intervalSaved, setIntervalSaved] = useState(false);

  useEffect(() => {
    if (user) setInterval_(user.notify_interval_hours);
  }, [user]);

  const handleGetLink = async () => {
    setLinkLoading(true);
    try {
      const res = await getTelegramLink();
      setTelegramLink(res.link);
    } finally {
      setLinkLoading(false);
    }
  };

  const handleUnlink = async () => {
    setUnlinkLoading(true);
    try {
      await unlinkTelegram();
      await refreshUser();
      setTelegramLink(null);
    } finally {
      setUnlinkLoading(false);
    }
  };

  const handleSaveInterval = async () => {
    setIntervalSaving(true);
    try {
      await updateMe({ notify_interval_hours: interval });
      await refreshUser();
      setIntervalSaved(true);
      setTimeout(() => setIntervalSaved(false), 2500);
    } finally {
      setIntervalSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-gray-100">Settings</h1>

      {/* ── Telegram connection ─────────────────────────────────────────── */}
      <section className="rounded-2xl bg-gray-800/60 border border-gray-700/50 p-5 flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <Send className="w-4 h-4 text-gold-400" />
          <h2 className="text-base font-semibold text-gray-100">Telegram Notifications</h2>
        </div>

        {user?.telegram_chat_id ? (
          /* Already connected */
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 text-emerald-400 text-sm font-medium">
              <CheckCircle className="w-4 h-4" />
              Telegram is connected
            </div>
            {user.telegram_connected_at && (
              <p className="text-xs text-gray-500">
                Connected on{" "}
                {new Date(user.telegram_connected_at).toLocaleDateString("en-US", {
                  dateStyle: "long",
                })}
              </p>
            )}
            <p className="text-sm text-gray-400">
              Price summaries will be sent every{" "}
              <span className="text-gold-400 font-medium">{user.notify_interval_hours} hours</span> to
              your Telegram.
            </p>
            <button
              onClick={handleUnlink}
              disabled={unlinkLoading}
              className="flex items-center gap-1.5 text-xs text-red-400 hover:text-red-300 disabled:opacity-50 self-start transition-colors"
            >
              <Unlink className="w-3.5 h-3.5" />
              {unlinkLoading ? "Unlinking…" : "Disconnect Telegram"}
            </button>
          </div>
        ) : (
          /* Not connected */
          <div className="flex flex-col gap-3">
            <p className="text-sm text-gray-400">
              Connect your Telegram account to receive automated gold price alerts.
            </p>

            <ol className="text-sm text-gray-400 list-decimal list-inside space-y-1">
              <li>Click <span className="text-gray-200 font-medium">Generate Link</span> below</li>
              <li>Open the link — it launches Telegram and starts a chat with the bot</li>
              <li>Press <span className="text-gray-200 font-medium">Start</span> in Telegram</li>
              <li>Come back here and refresh — the connection is instant</li>
            </ol>

            {telegramLink ? (
              <a
                href={telegramLink}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-sm font-medium text-gold-400 hover:text-gold-300 transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
                Open Telegram to connect
              </a>
            ) : (
              <button
                onClick={handleGetLink}
                disabled={linkLoading}
                className="self-start bg-gold-600 hover:bg-gold-500 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
              >
                {linkLoading ? "Generating…" : "Generate Link"}
              </button>
            )}

            {telegramLink && (
              <button
                onClick={refreshUser}
                className="self-start text-xs text-gray-400 hover:text-gray-200 underline"
              >
                I've connected — refresh status
              </button>
            )}
          </div>
        )}
      </section>

      {/* ── Notification interval ───────────────────────────────────────── */}
      <section className="rounded-2xl bg-gray-800/60 border border-gray-700/50 p-5 flex flex-col gap-4">
        <h2 className="text-base font-semibold text-gray-100">Summary Interval</h2>
        <p className="text-sm text-gray-400">
          How often you want to receive the periodic price summary on Telegram.
        </p>

        <div className="flex items-center gap-3">
          <input
            type="number"
            min={1}
            max={8760}
            value={interval}
            onChange={(e) => setInterval_(Number(e.target.value))}
            className="w-24 bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-gold-500"
          />
          <span className="text-sm text-gray-400">hours</span>
          <span className="text-xs text-gray-600">
            (48 = every 2 days, the recommended default)
          </span>
        </div>

        <button
          onClick={handleSaveInterval}
          disabled={intervalSaving}
          className="self-start bg-gold-600 hover:bg-gold-500 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          {intervalSaving ? "Saving…" : intervalSaved ? "✓ Saved" : "Save"}
        </button>
      </section>

      {/* ── Account info ────────────────────────────────────────────────── */}
      <section className="rounded-2xl bg-gray-800/60 border border-gray-700/50 p-5 flex flex-col gap-2">
        <h2 className="text-base font-semibold text-gray-100">Account</h2>
        <p className="text-sm text-gray-400">
          <span className="text-gray-500 mr-2">Email</span>
          {user?.email}
        </p>
        {user?.full_name && (
          <p className="text-sm text-gray-400">
            <span className="text-gray-500 mr-2">Name</span>
            {user.full_name}
          </p>
        )}
      </section>
    </div>
  );
}
