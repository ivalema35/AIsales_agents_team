import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { ArrowLeft, Target, Users, Check, Mail, MessageCircle, Eye, MessageSquareReply, XCircle } from "lucide-react";
import { api } from "../api/client";
import { CampaignReviewCard } from "../components/DailyReviewPanel";
import Badge from "../components/ui/Badge";
import { statusBadgeClass, statusLabel } from "../lib/statusColors";
import { industryLabel } from "../lib/targetSegment";
import { relativeTime } from "../lib/relativeTime";
import { useConfirm } from "../lib/ConfirmContext";
import { useToast } from "../lib/ToastContext";

const CAMPAIGN_STATUS = {
  PROPOSED: {
    label: "Draft",
    blurb: "Still marked draft — finding leads does not mean it was formally approved.",
  },
  APPROVED: {
    label: "Approved",
    blurb: "You formally approved this plan.",
  },
  RUNNING: {
    label: "Running",
    blurb: "Actively finding and working leads for this campaign.",
  },
  COMPLETED: {
    label: "Finished",
    blurb: "This campaign has reached its goal or been closed out.",
  },
  PAUSED: {
    label: "Paused",
    blurb: "On hold — nothing new will go out until you resume.",
  },
};

const TIER_PLAIN = {
  HOT: "High priority",
  WARM: "Worth a look",
  COLD: "Low priority",
};

// 2026-09-08, real gap the user found live: the campaign-level "Opened: 1" stat is a
// real, correct count (compute_campaign_metrics), but told a human nothing about WHICH
// lead that open belonged to -- the only way to find out was opening every single lead's
// own page and reading its full timeline. `l.outreach` (backend api/leads.py) carries
// the exact same `derive_delivery_state()` value the Lead Detail timeline already shows,
// so this never disagrees with that page -- just summarized into one glance-able cell.
const CHANNEL_ICON = { EMAIL: Mail, WHATSAPP: MessageCircle };

const OUTREACH_STATE_STYLE = {
  Replied: { variant: "SUCCESS", label: "Replied", icon: MessageSquareReply },
  Seen: { variant: "WARM", label: "Opened", icon: Eye },
  Delivered: { variant: "NEUTRAL", label: "Delivered", icon: null },
  Sent: { variant: "NEUTRAL", label: "Sent", icon: null },
  Failed: { variant: "DANGER", label: "Failed to send", icon: XCircle },
};

function OutreachCell({ outreach }) {
  if (!outreach) {
    return <span className="text-ink-500">Not sent yet</span>;
  }
  const style = OUTREACH_STATE_STYLE[outreach.state] || OUTREACH_STATE_STYLE.Sent;
  const ChannelIcon = CHANNEL_ICON[outreach.channel];
  const StateIcon = style.icon;
  const timestamp = outreach.state === "Seen" && outreach.read_at ? outreach.read_at : outreach.sent_at;
  const title = outreach.state === "Seen" && outreach.read_at
    ? `Opened ${outreach.read_at} (sent ${outreach.sent_at})`
    : `Sent ${outreach.sent_at}`;
  return (
    <div className="flex flex-col gap-0.5" title={title}>
      <Badge variant={style.variant} className="w-fit gap-1">
        {StateIcon && <StateIcon size={11} />}
        {style.label}
      </Badge>
      <span className="flex items-center gap-1 text-[10px] text-ink-500">
        {ChannelIcon && <ChannelIcon size={10} />}
        {outreach.channel === "WHATSAPP" ? "WhatsApp" : "Email"} · {relativeTime(timestamp)}
      </span>
    </div>
  );
}

function shortLocation(text) {
  if (!text) return null;
  const t = String(text).trim();
  if (t.length <= 56) return t;
  return `${t.slice(0, 54)}…`;
}

// UI Phase 16 revision (2026-09-02) -- "hum calendar se campaign open karke wahi sare leads
// data aur progress dekhne wale hain... campaign-wise hi leads dekhenge... wahi se main lead
// page me jaunga." This is that page: everything about ONE campaign -- its target, its
// progress toward lead_count_goal, today's find + how many were actually worth pursuing,
// its daily review (moved here from the old Dashboard-wide DailyReviewPanel), and its own
// lead list, each row linking to the existing Lead Detail page. Leads.jsx's own full list
// stays on disk for browsing outside any campaign context; this is the new entry point.
export default function CampaignDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const confirm = useConfirm();
  const toast = useToast();
  const [campaign, setCampaign] = useState(null);
  const [product, setProduct] = useState(null);
  const [leads, setLeads] = useState(null);
  const [error, setError] = useState(null);
  const [approving, setApproving] = useState(false);

  function refresh() {
    api.getCampaign(id).then(setCampaign).catch((err) => setError(err.message));
    api.listLeads({ campaign_id: id, per_page: 500 }).then((r) => setLeads(r.leads)).catch(() => {});
  }

  useEffect(refresh, [id]);

  useEffect(() => {
    if (campaign?.product_id) {
      api.getProduct(campaign.product_id).then(setProduct).catch(() => {});
    }
  }, [campaign?.product_id]);

  async function approveCampaign() {
    const ok = await confirm({
      title: "Approve this campaign?",
      message:
        `Mark "${campaign.name}" as approved? This only updates the campaign status label. ` +
        `Leads can already be found while status is still Draft — approving does not start discovery by itself.`,
      confirmLabel: "Mark as approved",
    });
    if (!ok) return;
    setApproving(true);
    try {
      const updated = await api.updateCampaign(id, { status: "APPROVED" });
      setCampaign(updated);
      toast.success("Campaign approved");
    } catch (err) {
      toast.error(err.message.replace(/^\d+\s*/, ""));
    } finally {
      setApproving(false);
    }
  }

  if (error) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-6 text-sm text-alert-600">
        Couldn't reach the backend: {error}
      </div>
    );
  }
  if (!campaign) {
    return <div className="mx-auto max-w-5xl px-6 py-6 text-sm text-ink-500">Loading…</div>;
  }

  const target = campaign.target_segment || {};
  const hasTarget = target.industry || target.location;
  const goal = campaign.lead_count_goal;
  const found = campaign.lead_summary?.total || 0;
  const progressPct = goal ? Math.min(100, Math.round((found / goal) * 100)) : 0;
  const statusMeta = CAMPAIGN_STATUS[campaign.status] || {
    label: campaign.status,
    blurb: null,
  };
  const foundToday = campaign.lead_summary?.found_today || 0;
  const qualifiedToday = campaign.lead_summary?.qualified_today || 0;
  const sent = campaign.metrics?.sent || 0;
  const opened = campaign.metrics?.opened || 0;
  const replied = campaign.metrics?.replied || 0;
  const hot = campaign.metrics?.hot || 0;

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 px-6 py-6">
      <Link to="/" className="flex w-fit items-center gap-1.5 text-xs font-medium text-ink-500 hover:text-ink-900">
        <ArrowLeft size={13} /> Back to Dashboard
      </Link>

      {/* Campaign snapshot — what a non-tech user should grasp first */}
      <div className="rounded-xl border border-line bg-parchment-raised p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <h1 className="font-display text-xl font-semibold text-ink-900">{campaign.name}</h1>
            <p className="mt-1 text-sm text-ink-500">{product?.title || "…"}</p>
          </div>
          <div className="shrink-0 text-right">
            <span className="inline-flex rounded-full bg-gold-100 px-3 py-1 text-xs font-semibold text-gold-700">
              {statusMeta.label}
            </span>
            {statusMeta.blurb && (
              <p className="mt-1.5 max-w-[14rem] text-[11px] leading-snug text-ink-500">{statusMeta.blurb}</p>
            )}
          </div>
        </div>

        {hasTarget ? (
          <div className="mt-4 rounded-md border border-line bg-parchment p-3">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-500">Who this targets</p>
            <p className="mt-1 flex items-start gap-1.5 text-sm text-ink-800">
              <Target size={14} className="mt-0.5 shrink-0 text-ink-500" />
              <span>
                {industryLabel(target) || "Businesses"}
                {target.location ? ` in ${target.location}` : ""}
              </span>
            </p>
          </div>
        ) : (
          <div className="mt-4 rounded-md border border-dashed border-line bg-parchment p-3">
            <p className="text-sm text-ink-600">
              Targeting not set yet — approve an AI suggestion below, or edit who this campaign should find.
            </p>
          </div>
        )}

        {goal != null && (
          <div className="mt-4">
            <div className="flex items-center justify-between gap-2 text-xs">
              <span className="font-medium text-ink-700">
                {found} of {goal} leads found
              </span>
              <span className="tabular-nums text-ink-500">{progressPct}% of goal</span>
            </div>
            <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-parchment-raised-2">
              <div className="h-full rounded-full bg-gold-600 transition-all" style={{ width: `${progressPct}%` }} />
            </div>
          </div>
        )}

        <div className="mt-4 grid grid-cols-2 gap-2 border-t border-line pt-4 sm:grid-cols-3 lg:grid-cols-6">
          <StatChip label="Found today" value={foundToday} />
          <StatChip label="Worth pursuing today" value={qualifiedToday} hint="Warm or hot after scoring" />
          <StatChip label="Messages sent" value={sent} />
          <StatChip label="Opened" value={opened} />
          <StatChip label="Replied" value={replied} />
          {hot > 0 && <StatChip label="Hot interest" value={hot} emphasize />}
        </div>

        {campaign.status === "PROPOSED" && (
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-md border border-line bg-parchment px-4 py-3">
            <div className="min-w-0">
              <p className="text-sm font-semibold text-ink-900">
                {found > 0 ? "Mark this plan as approved?" : "Approve this campaign plan?"}
              </p>
              <p className="mt-0.5 text-xs leading-relaxed text-ink-600">
                {found > 0
                  ? `Leads already appeared because discovery also runs on draft campaigns once targeting is set — not because status was Approved. Formally approving just records that you're happy with this plan (${found} lead${found === 1 ? "" : "s"} so far).`
                  : "Discovery can find leads even while status is Draft, as soon as who-to-target is set. Approving is your formal OK on the plan — it is separate from AI suggestion Approves below."}
              </p>
            </div>
            <button
              type="button"
              onClick={approveCampaign}
              disabled={approving}
              className="inline-flex shrink-0 items-center gap-1.5 rounded-md bg-ink-900 px-4 py-2 text-xs font-semibold text-parchment-raised hover:opacity-90 disabled:opacity-50"
            >
              <Check size={14} />
              {approving ? "Approving…" : "Mark as approved"}
            </button>
          </div>
        )}
      </div>

      <CampaignReviewCard campaign={campaign} onApproved={refresh} />

      <div className="rounded-xl border border-line bg-parchment-raised p-5 shadow-sm">
        <div className="mb-1 flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="flex items-center gap-2 font-display text-lg font-semibold text-ink-900">
              <Users size={18} className="text-ink-500" />
              Businesses in this campaign
            </h2>
            <p className="mt-0.5 text-xs text-ink-500">
              Click a row to open the full lead page. Priority shows how strong the fit looks; Message shows whether your outreach was sent, opened, or replied to.
            </p>
          </div>
          {leads && leads.length > 0 && (
            <span className="text-xs tabular-nums text-ink-500">
              {leads.length} business{leads.length === 1 ? "" : "es"}
            </span>
          )}
        </div>

        {leads === null ? (
          <div className="mt-3 h-16 animate-pulse rounded-lg bg-parchment-raised-2" />
        ) : leads.length === 0 ? (
          <div className="mt-4 flex flex-col items-center gap-2 py-8 text-center">
            <Users className="text-ink-500" size={28} />
            <p className="text-sm font-medium text-ink-700">No businesses found yet</p>
            <p className="max-w-sm text-xs leading-relaxed text-ink-500">
              Discovery will list companies here once it finds matches for this campaign&apos;s target.
            </p>
          </div>
        ) : (
          <div className="mt-3 overflow-x-auto rounded-lg border border-line">
            <table className="w-full text-left text-xs">
              <thead className="bg-parchment-raised-2 text-[10px] font-semibold uppercase tracking-wide text-ink-500">
                <tr>
                  <th className="px-3 py-2.5">Business</th>
                  <th className="px-3 py-2.5">Location</th>
                  <th className="px-3 py-2.5">Stage</th>
                  <th className="px-3 py-2.5">Priority</th>
                  <th className="px-3 py-2.5">Message</th>
                </tr>
              </thead>
              <tbody>
                {leads.map((l) => {
                  const tier = l.score?.tier;
                  const points = l.score?.score;
                  return (
                    <tr
                      key={l.id}
                      role="button"
                      tabIndex={0}
                      onClick={() => navigate(`/leads/${l.id}`)}
                      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && navigate(`/leads/${l.id}`)}
                      className="cursor-pointer border-t border-line bg-parchment-raised hover:bg-parchment"
                    >
                      <td className="px-3 py-2.5 font-medium text-ink-900">{l.company_name}</td>
                      <td className="max-w-[14rem] px-3 py-2.5 text-ink-500" title={l.region_location || undefined}>
                        {shortLocation(l.region_location) || "—"}
                      </td>
                      <td className="px-3 py-2.5">
                        <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold ${statusBadgeClass(l.status)}`}>
                          {statusLabel(l.status)}
                        </span>
                      </td>
                      <td className="px-3 py-2.5">
                        {tier ? (
                          <div className="flex flex-col gap-0.5">
                            <div className="flex flex-wrap items-center gap-1.5">
                              <Badge variant={tier}>{tier}</Badge>
                              {points != null && (
                                <span className="tabular-nums text-[11px] text-ink-500">{points}/100</span>
                              )}
                            </div>
                            <span className="text-[10px] text-ink-500">{TIER_PLAIN[tier] || ""}</span>
                          </div>
                        ) : (
                          <span className="text-ink-500">Not scored yet</span>
                        )}
                      </td>
                      <td className="px-3 py-2.5">
                        <OutreachCell outreach={l.outreach} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function StatChip({ label, value, hint, emphasize }) {
  return (
    <div
      className={`rounded-md border px-2.5 py-2 ${
        emphasize ? "border-alert-600/30 bg-alert-100/50" : "border-line bg-parchment"
      }`}
      title={hint}
    >
      <p className={`text-[10px] font-medium uppercase tracking-wide ${emphasize ? "text-alert-700" : "text-ink-500"}`}>
        {label}
      </p>
      <p className={`mt-0.5 font-display text-lg font-semibold tabular-nums ${emphasize ? "text-alert-700" : "text-ink-900"}`}>
        {value}
      </p>
    </div>
  );
}
