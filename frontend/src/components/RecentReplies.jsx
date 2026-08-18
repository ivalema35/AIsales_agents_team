import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Mail, MessageCircle, Check } from "lucide-react";
import { api } from "../api/client";
import { relativeTime } from "../lib/relativeTime";

function ReplyColumn({ title, icon: Icon, accent, replies, onMarkRead }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center gap-2 border-b border-slate-100 px-4 py-2.5">
        <Icon size={14} className={accent} />
        <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
        <span className="ml-auto rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">
          {replies.length}
        </span>
      </div>
      {replies.length === 0 ? (
        <p className="px-4 py-8 text-center text-sm text-slate-400">No replies yet.</p>
      ) : (
        <div className="flex flex-col divide-y divide-slate-100">
          {replies.map((r) => (
            <div key={r.id} className="flex items-start gap-2 px-4 py-3 transition-colors hover:bg-slate-50">
              <Link to={`/leads/${r.lead_id}`} className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate text-sm font-medium text-slate-800">{r.company_name}</span>
                  <span className="shrink-0 text-[11px] text-slate-400">{relativeTime(r.replied_at)}</span>
                </div>
                <p className="mt-1 line-clamp-1 text-xs text-slate-500">"{r.message}"</p>
                {r.intent_detected && (
                  <span className="mt-1 inline-block w-fit rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
                    {r.intent_detected.replace(/_/g, " ")}
                  </span>
                )}
              </Link>
              <button
                onClick={() => onMarkRead(r.id)}
                title="Mark as read"
                className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-slate-300 transition-colors hover:bg-emerald-50 hover:text-emerald-600"
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
      <h2 className="mb-3 text-sm font-semibold text-slate-700">Recent replies</h2>
      {error && <p className="mb-2 text-xs text-red-600">{error}</p>}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <ReplyColumn
          title="WhatsApp"
          icon={MessageCircle}
          accent="text-emerald-500"
          replies={data.WHATSAPP || []}
          onMarkRead={markRead}
        />
        <ReplyColumn
          title="Email"
          icon={Mail}
          accent="text-slate-500"
          replies={data.EMAIL || []}
          onMarkRead={markRead}
        />
      </div>
    </div>
  );
}
