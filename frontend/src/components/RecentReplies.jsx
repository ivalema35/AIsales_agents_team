import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Mail, MessageCircle, Check } from "lucide-react";
import { api } from "../api/client";
import { relativeTime } from "../lib/relativeTime";

function ReplyColumn({ title, icon: Icon, accent, replies, onMarkRead }) {
  return (
    <div className="rounded-lg border border-line bg-parchment-raised shadow-sm">
      <div className="flex items-center gap-2 border-b border-line px-4 py-2.5">
        <Icon size={14} className={accent} />
        <h3 className="text-sm font-semibold text-ink-900">{title}</h3>
        <span className="ml-auto rounded-full bg-parchment-raised-2 px-2 py-0.5 text-xs font-medium text-ink-500">
          {replies.length}
        </span>
      </div>
      {replies.length === 0 ? (
        <p className="px-4 py-8 text-center text-sm text-ink-500">No replies yet.</p>
      ) : (
        <div className="flex flex-col divide-y divide-line">
          {replies.map((r) => (
            <div key={r.id} className="flex items-start gap-2 px-4 py-3 transition-colors hover:bg-parchment">
              <Link to={`/leads/${r.lead_id}`} className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate text-sm font-medium text-ink-900">{r.company_name}</span>
                  <span className="shrink-0 font-mono text-[11px] text-ink-500">{relativeTime(r.replied_at)}</span>
                </div>
                <p className="mt-1 line-clamp-1 text-xs text-ink-500">"{r.message}"</p>
                {r.intent_detected && (
                  <span className="mt-1 inline-block w-fit rounded-full bg-parchment-raised-2 px-2 py-0.5 text-[10px] font-semibold text-ink-700">
                    {r.intent_detected.replace(/_/g, " ")}
                  </span>
                )}
              </Link>
              <button
                onClick={() => onMarkRead(r.id)}
                title="Mark as read"
                className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-ink-500/40 transition-colors hover:bg-good-100 hover:text-good-600"
              >
                <Check size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// The two channels leads actually write back on, kept as separate grids (not one merged
// feed) per the user's own request -- WhatsApp and email replies have different reply
// speed/etiquette expectations, so scanning them separately reads more naturally than
// interleaving. One row per lead (its LATEST UNREAD reply), most recent first --
// "Mark as read" (PATCH /inbound/<id>/read) is what drops a reply off this list; there's
// no separate archive/dismiss state, the read flag on the message itself is the signal.
export default function RecentReplies() {
  const [data, setData] = useState({ EMAIL: [], WHATSAPP: [] });
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getRecentReplies().then(setData).catch((err) => setError(err.message));
  }, []);

  async function markRead(conversationId) {
    // Optimistic -- remove from both channel arrays immediately (it's only ever in one,
    // but a filter on both is cheap and avoids needing to know which channel it was in).
    setData((prev) => ({
      EMAIL: prev.EMAIL.filter((r) => r.id !== conversationId),
      WHATSAPP: prev.WHATSAPP.filter((r) => r.id !== conversationId),
    }));
    try {
      await api.markReplyRead(conversationId);
    } catch (err) {
      setError(err.message);
      api.getRecentReplies().then(setData).catch(() => {}); // resync on failure
    }
  }

  return (
    <div>
      <h2 className="mb-3 font-display text-sm font-semibold text-ink-700">Recent replies</h2>
      {error && <p className="mb-2 text-xs text-alert-600">{error}</p>}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <ReplyColumn
          title="WhatsApp"
          icon={MessageCircle}
          accent="text-good-600"
          replies={data.WHATSAPP || []}
          onMarkRead={markRead}
        />
        <ReplyColumn
          title="Email"
          icon={Mail}
          accent="text-ink-500"
          replies={data.EMAIL || []}
          onMarkRead={markRead}
        />
      </div>
    </div>
  );
}
