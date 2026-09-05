import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Inbox, Copy, Send, X, CheckCircle2 } from "lucide-react";
import { api } from "../api/client";
import { InstagramIcon, FacebookIcon, LinkedinIcon } from "../lib/socialIcons";

// Phase 10 Step 10.3 -- the human-facing "to-do" surface for the draft-and-queue design:
// AI drafts a LinkedIn/Instagram/Facebook message per lead (from that lead's own detail
// page), QC gates it, and only a QC-approved draft ever lands here. A human works through
// this list, sends each one manually from their own real account, and marks it sent.
// There is deliberately no "send" button anywhere in this codebase for these platforms.
const PLATFORM_ICON = { LINKEDIN: LinkedinIcon, INSTAGRAM: InstagramIcon, FACEBOOK: FacebookIcon };

function QueueCard({ item, onRefresh }) {
  const [acting, setActing] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);
  const Icon = PLATFORM_ICON[item.platform] || Inbox;

  async function copyText() {
    try {
      await navigator.clipboard.writeText(item.message_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard permission denied -- text is still visible to select manually */
    }
  }

  async function act(fn) {
    setActing(true);
    setError(null);
    try {
      await fn(item.id);
      onRefresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setActing(false);
    }
  }

  return (
    <div className="rounded-lg border border-line bg-parchment-raised p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-semibold text-ink-900">
          <Icon size={14} className="text-ink-500" /> {item.platform}
          <span className="text-ink-500">·</span>
          <Link to={`/leads/${item.lead_id}`} className="text-ink-700 hover:text-ink-900 hover:underline">
            {item.lead_company_name || item.lead_id}
          </Link>
        </div>
        <span className="font-mono text-[11px] text-ink-500">{new Date(item.created_at.replace(" ", "T") + "Z").toLocaleString()}</span>
      </div>
      <p className="mt-2.5 whitespace-pre-wrap rounded-md bg-parchment-raised-2 p-3 text-xs leading-relaxed text-ink-700">
        {item.message_text}
      </p>
      {item.reasoning && <p className="mt-1.5 text-[11px] italic text-ink-500">Why: {item.reasoning}</p>}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button
          onClick={copyText}
          className="flex items-center gap-1 rounded-md border border-line px-2.5 py-1.5 text-xs font-medium text-ink-700 transition-colors hover:bg-parchment-raised-2"
        >
          <Copy size={12} /> {copied ? "Copied" : "Copy text"}
        </button>
        <button
          onClick={() => act(api.markSocialSent)}
          disabled={acting}
          title="Confirm you sent this manually from your own account"
          className="flex items-center gap-1 rounded-md bg-ink-900 px-2.5 py-1.5 text-xs font-medium text-parchment-raised transition-colors hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Send size={12} /> Mark as Sent
        </button>
        <button
          onClick={() => act(api.dismissSocialDraft)}
          disabled={acting}
          className="flex items-center gap-1 rounded-md px-2.5 py-1.5 text-xs font-medium text-ink-500 transition-colors hover:bg-parchment-raised-2 hover:text-ink-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <X size={12} /> Dismiss
        </button>
        {error && <span className="text-xs text-alert-600">{error}</span>}
      </div>
    </div>
  );
}

export default function SocialQueue() {
  const [items, setItems] = useState(null);
  const [error, setError] = useState(null);

  function refresh() {
    api.listSocialQueue({ status: "QUEUED" }).then(setItems).catch((err) => setError(err.message));
  }

  useEffect(refresh, []);

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-5 px-6 py-6">
      <div>
        <h1 className="font-display text-lg font-semibold text-ink-900">Social Outreach Queue</h1>
        <p className="mt-1 text-xs text-ink-500">
          AI-drafted LinkedIn / Instagram / Facebook messages, QC-approved and waiting for a human to
          send manually from their own real account, then mark sent here. Draft a new one from any
          lead's own page under "Social outreach".
        </p>
      </div>

      {error && <p className="text-sm text-alert-600">{error}</p>}
      {!items && !error && <p className="text-sm text-ink-500">Loading…</p>}

      {items && items.length === 0 && (
        <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-line bg-parchment-raised py-12 text-center">
          <CheckCircle2 className="text-ink-500" size={28} />
          <p className="text-sm text-ink-500">Nothing queued right now.</p>
        </div>
      )}

      {items && items.length > 0 && (
        <div className="flex flex-col gap-3">
          {items.map((item) => (
            <QueueCard key={item.id} item={item} onRefresh={refresh} />
          ))}
        </div>
      )}
    </div>
  );
}
