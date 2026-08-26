import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, X, Users, Mail, Phone, Send, BellOff } from "lucide-react";
import { InstagramIcon, FacebookIcon, LinkedinIcon } from "../lib/socialIcons";
import { api } from "../api/client";
import Badge from "../components/ui/Badge";
import { statusBadgeClass } from "../lib/statusColors";
import { intentBadgeClass } from "../lib/intentColors";
import { relativeTime } from "../lib/relativeTime";
import { useConfirm } from "../lib/ConfirmContext";
import { TIER_BG, TIER_BORDER } from "../lib/tierColors";

const PER_PAGE = 50;
const SEARCH_DEBOUNCE_MS = 350;
const STATUSES = [
  "DISCOVERED", "ENRICHED", "REVIEWED", "SCORED", "OUTREACHING",
  "OUTREACHED", "ENGAGED", "HOT_LEAD", "CONVERTED", "REJECTED",
];
const TIERS = ["HOT", "WARM", "COLD"];
// Bolder filled version of Badge.jsx's tier colors -- a selected filter pill needs to
// read as "active/pressed," which the light Badge tint alone doesn't convey.
const TIER_PILL_ACTIVE = {
  HOT: "bg-red-600 text-white ring-1 ring-inset ring-red-600",
  WARM: "bg-amber-500 text-white ring-1 ring-inset ring-amber-500",
  COLD: "bg-slate-600 text-white ring-1 ring-inset ring-slate-600",
};
const TIER_PILL_INACTIVE = "bg-white text-slate-600 ring-1 ring-inset ring-slate-200 hover:bg-slate-50";

function FilterSelect({ value, onChange, options, placeholder }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 focus:border-slate-400 focus:outline-none"
    >
      <option value="">{placeholder}</option>
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}

function CompanyAvatar({ name }) {
  return (
    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-100 text-[10px] font-semibold text-slate-500">
      {name.slice(0, 2).toUpperCase()}
    </div>
  );
}

function LeadRow({ lead, productTitle, filterQs, onSent }) {
  const navigate = useNavigate();
  const confirm = useConfirm();
  const [sending, setSending] = useState(false);
  const intent = lead.status === "HOT_LEAD" ? lead.latest_reply_intent : null;
  const canSend = lead.score && (lead.primary_email || lead.primary_phone) && !lead.is_suppressed
    && lead.status !== "OUTREACHING";
  const tier = lead.score?.tier;
  // Same tinted-row + left-accent treatment as the Kanban card (TIER_BG/TIER_BORDER,
  // shared from lib/tierColors.js) -- a HOT lead should read as HOT the same way
  // whether you're looking at the board or this table, not a plain badge in one and a
  // colored card in the other. Opted-out overrides tier here too, same priority as the
  // card.
  const rowBg = lead.is_suppressed ? "bg-slate-100" : tier ? TIER_BG[tier] : "";
  const accentColor = lead.is_suppressed ? "#94a3b8" : tier ? TIER_BORDER[tier] : null;

  function openLead() {
    navigate(`/leads/${lead.id}${filterQs ? `?${filterQs}` : ""}`);
  }

  async function sendOutreach(e) {
    e.stopPropagation();
    const ok = await confirm({
      title: "Send real outreach?",
      message: `Send REAL outreach to ${lead.company_name} now (${lead.primary_email || "no email"} / ` +
        `${lead.primary_phone || "no phone"})? This is a real send, not a simulation.`,
      confirmLabel: "Send now",
    });
    if (!ok) return;
    setSending(true);
    try {
      await api.triggerOutreach(lead.id);
      onSent?.(lead.id);
    } catch {
      // Same-shape failure as everywhere else this button exists (LeadCard/LeadDetail) --
      // a disabled/no-op button on retry is enough feedback here; the table row doesn't
      // have room for a per-row result banner the way a card does.
    } finally {
      setSending(false);
    }
  }

  return (
    <tr
      onClick={openLead}
      // brightness (not a hover:bg- override) so the hover state darkens WHATEVER the
      // row's own tint already is, tier-colored or plain white, instead of a flat gray
      // hover erasing the tier wash every time the cursor passes over.
      className={`cursor-pointer transition-all hover:brightness-95 ${rowBg} ${lead.is_suppressed ? "opacity-60" : ""}`}
    >
      <td
        className={`px-4 py-2.5 ${accentColor ? "border-l-[3px]" : ""}`}
        style={accentColor ? { borderLeftColor: accentColor } : undefined}
      >
        <div className="flex items-center gap-2.5 font-medium text-slate-800">
          <CompanyAvatar name={lead.company_name} />
          <span className="line-clamp-1 hover:underline">{lead.company_name}</span>
          {lead.reference_code && (
            <span
              title="Reference code -- quote this in alerts/conversation to identify this lead"
              className="shrink-0 rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] font-normal text-slate-500"
            >
              {lead.reference_code}
            </span>
          )}
          {lead.is_suppressed && <BellOff size={12} className="shrink-0 text-slate-400" title="Opted out -- do not contact" />}
        </div>
      </td>
      <td className="max-w-[160px] truncate px-4 py-2.5 text-slate-500">{productTitle(lead.product_id)}</td>
      <td className="px-4 py-2.5">
        <span className={`inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-[11px] font-semibold ${statusBadgeClass(lead.status)}`}>
          {lead.status.replace(/_/g, " ")}
        </span>
      </td>
      <td className="px-4 py-2.5">
        {intent ? (
          <span title={lead.latest_reply_message || undefined} className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1 ring-inset ${intentBadgeClass(intent)}`}>
            {intent.replace(/_/g, " ")}
          </span>
        ) : lead.score ? (
          <Badge variant={lead.score.tier}>{lead.score.tier}</Badge>
        ) : (
          <span className="text-slate-300">—</span>
        )}
      </td>
      <td className="px-4 py-2.5 text-right tabular-nums text-slate-700">
        {lead.score ? lead.score.score : <span className="text-slate-300">—</span>}
      </td>
      <td className="px-4 py-2.5">
        <div className="flex items-center gap-2.5 text-[11px] text-slate-400">
          {lead.primary_email && <span title={lead.primary_email}><Mail size={12} /></span>}
          {(lead.primary_phone || lead.whatsapp_number) && <span title={lead.primary_phone || lead.whatsapp_number}><Phone size={12} /></span>}
          {lead.instagram_url && <span title="Instagram"><InstagramIcon size={12} /></span>}
          {lead.facebook_url && <span title="Facebook"><FacebookIcon size={12} /></span>}
          {lead.linkedin_url && <span title="LinkedIn"><LinkedinIcon size={12} /></span>}
          {!lead.primary_email && !lead.primary_phone && !lead.whatsapp_number &&
           !lead.instagram_url && !lead.facebook_url && !lead.linkedin_url && (
            <span className="text-slate-300">—</span>
          )}
        </div>
      </td>
      <td className="max-w-[180px] truncate px-4 py-2.5 text-slate-500">{lead.region_location || "—"}</td>
      <td className="whitespace-nowrap px-4 py-2.5 text-slate-500">{relativeTime(lead.created_at)}</td>
      <td className="px-4 py-2.5">
        {canSend && (
          <button
            onClick={sendOutreach}
            disabled={sending}
            title="Send Outreach Now"
            className="flex h-6 w-6 items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Send size={13} />
          </button>
        )}
      </td>
    </tr>
  );
}

export default function Leads() {
  const [products, setProducts] = useState([]);
  const [productFilter, setProductFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [tierFilter, setTierFilter] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState(""); // debounced value that actually drives the fetch
  const [page, setPage] = useState(1);

  const [data, setData] = useState(null); // {leads, total, page, per_page, total_pages}
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.listProducts().then(setProducts).catch(() => {});
  }, []);

  // Debounce the search box -- firing a request on every keystroke would spam the
  // backend and flash the table with intermediate junk results while typing.
  useEffect(() => {
    const t = setTimeout(() => {
      setSearch(searchInput);
      setPage(1);
    }, SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(t);
  }, [searchInput]);

  function fetchLeads() {
    setLoading(true);
    const params = { page, per_page: PER_PAGE };
    if (productFilter) params.product_id = productFilter;
    if (statusFilter) params.status = statusFilter;
    if (tierFilter) params.tier = tierFilter;
    if (search) params.search = search;
    api.listLeads(params)
      .then((res) => { setData(res); setError(null); })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(fetchLeads, [page, productFilter, statusFilter, tierFilter, search]); // eslint-disable-line react-hooks/exhaustive-deps

  // A row's status/badge changes after a send (SCORED -> OUTREACHING) -- refetch this
  // page rather than hand-patch one row, since the send can also affect which page a
  // filtered view should show the lead on.
  function handleSent() {
    fetchLeads();
  }

  // Any filter change invalidates the current page number (a page 4 filtered down to
  // 1 page would otherwise render nothing with no obvious reason why) -- reset to 1.
  function handleProductFilter(v) { setProductFilter(v); setPage(1); }
  function handleStatusFilter(v) { setStatusFilter(v); setPage(1); }
  function handleTierFilter(v) { setTierFilter((prev) => (prev === v ? "" : v)); setPage(1); }
  function clearAll() {
    setProductFilter(""); setStatusFilter(""); setTierFilter("");
    setSearchInput(""); setSearch(""); setPage(1);
  }

  const productTitle = (id) => products.find((p) => p.id === id)?.title || id;
  const anyFilterActive = productFilter || statusFilter || tierFilter || search;

  // Carried into each lead's detail-page link so its own Prev/Next walks through this
  // SAME filtered list, not the unfiltered whole table -- "next" should mean what the
  // user is actually looking at here, not everything.
  const filterQs = useMemo(() => {
    const p = {};
    if (productFilter) p.product_id = productFilter;
    if (statusFilter) p.status = statusFilter;
    if (tierFilter) p.tier = tierFilter;
    if (search) p.search = search;
    return new URLSearchParams(p).toString();
  }, [productFilter, statusFilter, tierFilter, search]);

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-6">
      <div>
        <h1 className="text-lg font-semibold text-slate-900">Leads</h1>
        <p className="mt-0.5 text-sm text-slate-500">
          {data ? `${data.total} lead${data.total === 1 ? "" : "s"}${anyFilterActive ? " matching filters" : " total"}` : "Loading…"}
        </p>
      </div>

      <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative min-w-[240px] flex-1">
            <Search size={14} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search company, ref code, email, phone, region…"
              className="w-full rounded-md border border-slate-200 bg-white py-1.5 pl-8 pr-8 text-xs text-slate-700 placeholder:text-slate-400 focus:border-slate-400 focus:outline-none"
            />
            {searchInput && (
              <button
                onClick={() => setSearchInput("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-300 hover:text-slate-600"
                aria-label="Clear search"
              >
                <X size={13} />
              </button>
            )}
          </div>
          <FilterSelect
            value={productFilter}
            onChange={handleProductFilter}
            placeholder="All products"
            options={products.map((p) => ({ value: p.id, label: p.title }))}
          />
          <FilterSelect
            value={statusFilter}
            onChange={handleStatusFilter}
            placeholder="All statuses"
            options={STATUSES.map((s) => ({ value: s, label: s.replace(/_/g, " ") }))}
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3">
          <span className="text-[11px] font-medium uppercase tracking-wide text-slate-400">Tier</span>
          {TIERS.map((t) => (
            <button
              key={t}
              onClick={() => handleTierFilter(t)}
              className={`rounded-full px-2.5 py-1 text-[11px] font-semibold transition-colors ${
                tierFilter === t ? TIER_PILL_ACTIVE[t] : TIER_PILL_INACTIVE
              }`}
            >
              {t}
            </button>
          ))}
          {anyFilterActive && (
            <button
              onClick={clearAll}
              className="ml-auto flex items-center gap-1 text-[11px] font-medium text-slate-400 hover:text-slate-700"
            >
              <X size={12} /> Clear filters
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 ring-1 ring-red-100">
          Couldn't reach the backend: {error}
        </div>
      )}

      <div className={`overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm transition-opacity ${loading ? "opacity-60" : ""}`}>
        <table className="w-full min-w-[1000px] text-left text-xs">
          <thead>
            <tr className="border-b border-slate-200 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              <th className="px-4 py-2.5">Company</th>
              <th className="px-4 py-2.5">Product</th>
              <th className="px-4 py-2.5">Status</th>
              <th className="px-4 py-2.5">Tier / Intent</th>
              <th className="px-4 py-2.5 text-right">Score</th>
              <th className="px-4 py-2.5">Contact</th>
              <th className="px-4 py-2.5">Region</th>
              <th className="px-4 py-2.5">Discovered</th>
              <th className="px-4 py-2.5"></th>
            </tr>
          </thead>
          {/* A hairline divide-slate-100 nearly disappeared once rows started carrying
             their own tier-tinted background -- a colored row butting straight up
             against another read as one merged block instead of two distinct leads
             (user feedback). A visibly darker, slightly thicker divider fixes that
             regardless of what color sits on either side of it. */}
          <tbody className="divide-y-2 divide-slate-200">
            {!loading && data?.leads.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-12">
                  <div className="flex flex-col items-center gap-2 text-center">
                    <Users className="text-slate-300" size={28} />
                    <p className="text-slate-400">No leads match these filters.</p>
                    {anyFilterActive && (
                      <button onClick={clearAll} className="text-[11px] font-medium text-slate-500 hover:text-slate-800 hover:underline">
                        Clear filters
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            )}
            {(data?.leads || []).map((lead) => (
              <LeadRow key={lead.id} lead={lead} productTitle={productTitle} filterQs={filterQs} onSent={handleSent} />
            ))}
          </tbody>
        </table>
      </div>

      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-500">
            Page {data.page} of {data.total_pages}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={data.page <= 1}
              className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              ← Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
              disabled={data.page >= data.total_pages}
              className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
