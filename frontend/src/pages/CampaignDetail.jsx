import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { ArrowLeft, Target } from "lucide-react";
import { api } from "../api/client";
import { CampaignReviewCard } from "../components/DailyReviewPanel";
import Badge from "../components/ui/Badge";
import { statusBadgeClass } from "../lib/statusColors";

const STATUS_LABEL = {
  PROPOSED: "Proposed",
  APPROVED: "Approved",
  RUNNING: "Running",
  COMPLETED: "Completed",
  PAUSED: "Paused",
};

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
  const [campaign, setCampaign] = useState(null);
  const [product, setProduct] = useState(null);
  const [leads, setLeads] = useState(null);
  const [error, setError] = useState(null);

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

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 px-6 py-6">
      <Link to="/" className="flex w-fit items-center gap-1.5 text-xs font-medium text-ink-500 hover:text-ink-900">
        <ArrowLeft size={13} /> Back to Dashboard
      </Link>

      <div className="rounded-xl border border-line bg-parchment-raised p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="font-display text-xl font-semibold text-ink-900">{campaign.name}</h1>
            <p className="mt-1 text-sm text-ink-500">{product?.title || "…"}</p>
          </div>
          <span className="shrink-0 rounded-full bg-gold-100 px-3 py-1 text-xs font-semibold text-gold-700">
            {STATUS_LABEL[campaign.status] || campaign.status}
          </span>
        </div>

        {hasTarget && (
          <p className="mt-3 flex items-center gap-1.5 text-sm text-ink-700">
            <Target size={14} className="text-ink-500" />
            {target.industry || "—"}
            {target.location && ` in ${target.location}`}
          </p>
        )}

        {goal != null && (
          <div className="mt-3">
            <div className="flex items-center justify-between text-xs text-ink-500">
              <span>{found} of {goal} leads found</span>
              <span>{progressPct}%</span>
            </div>
            <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-parchment-raised-2">
              <div className="h-full bg-gold-600" style={{ width: `${progressPct}%` }} />
            </div>
          </div>
        )}

        <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1.5 border-t border-line pt-4 font-mono text-xs text-ink-700">
          <span>{campaign.lead_summary?.found_today || 0} found today</span>
          <span>{campaign.lead_summary?.qualified_today || 0} qualified today</span>
          <span className="text-ink-500">·</span>
          <span>{campaign.metrics?.sent || 0} sent</span>
          <span>{campaign.metrics?.opened || 0} opened</span>
          <span>{campaign.metrics?.replied || 0} replied</span>
          {campaign.metrics?.hot > 0 && <span className="text-alert-600">{campaign.metrics.hot} hot</span>}
        </div>
      </div>

      <CampaignReviewCard campaign={campaign} onApproved={refresh} />

      <div>
        <h2 className="mb-3 font-display text-lg font-semibold text-ink-900">Leads</h2>
        {leads === null ? (
          <div className="h-16 animate-pulse rounded-lg bg-parchment-raised-2" />
        ) : leads.length === 0 ? (
          <p className="text-xs text-ink-500">No leads yet -- discovery hasn't found any for this campaign.</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-line">
            <table className="w-full text-left text-xs">
              <thead className="bg-parchment-raised-2 text-[10px] font-semibold uppercase tracking-wide text-ink-500">
                <tr>
                  <th className="px-3 py-2">Business</th>
                  <th className="px-3 py-2">Region</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Tier</th>
                </tr>
              </thead>
              <tbody>
                {leads.map((l) => (
                  <tr
                    key={l.id}
                    role="button"
                    tabIndex={0}
                    onClick={() => navigate(`/leads/${l.id}`)}
                    onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && navigate(`/leads/${l.id}`)}
                    className="cursor-pointer border-t border-line bg-parchment-raised hover:bg-parchment-raised-2"
                  >
                    <td className="px-3 py-2 font-medium text-ink-900">{l.company_name}</td>
                    <td className="px-3 py-2 text-ink-500">{l.region_location || "—"}</td>
                    <td className="px-3 py-2">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${statusBadgeClass(l.status)}`}>
                        {l.status}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      {l.score ? <Badge variant={l.score.tier}>{l.score.tier}</Badge> : <span className="text-ink-500">—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
