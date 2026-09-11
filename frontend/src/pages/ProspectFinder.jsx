import { useEffect, useMemo, useState } from "react";
import {
  Search, Users, Mail, Phone, CheckCircle2, AlertCircle, ChevronDown, ChevronUp,
  MapPin, Sparkles,
} from "lucide-react";
import { api } from "../api/client";
import { LinkedinIcon } from "../lib/socialIcons";

// Phase 15 Step 15(B) -- standalone person search (not the leads funnel).
// 2026-09-10 UX: each past search is an expandable group card; opening it shows
// only that search's people. Flat "history + all prospects" was too techy.

function ConfidenceBadge({ confidence }) {
  if (confidence == null) return null;
  const pct = Math.round(confidence * 100);
  const strong = confidence >= 0.6;
  return (
    <span
      title={strong ? "Looks like a clean LinkedIn match" : "Weaker match — double-check before relying on this"}
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold ${
        strong ? "bg-good-100 text-good-700" : "bg-warm-100 text-warm-700"
      }`}
    >
      {strong ? <CheckCircle2 size={10} /> : <AlertCircle size={10} />}
      {pct}% {strong ? "likely" : "unverified"}
    </span>
  );
}

function formatWhen(raw) {
  if (!raw) return "";
  const d = new Date(String(raw).replace(" ", "T") + (String(raw).includes("Z") ? "" : "Z"));
  if (Number.isNaN(d.getTime())) return String(raw);
  // 2026-09-11, real user-caught bug: pinned to IST so this shows correctly regardless
  // of the viewing device's own OS/browser timezone setting -- display only.
  return d.toLocaleString(undefined, {
    month: "short", day: "numeric", year: "numeric",
    hour: "numeric", minute: "2-digit",
    timeZone: "Asia/Kolkata",
  });
}

function ProspectCard({ prospect, onRefresh }) {
  const [enriching, setEnriching] = useState(false);
  const [error, setError] = useState(null);

  async function enrich() {
    setEnriching(true);
    setError(null);
    try {
      await api.enrichProspect(prospect.id);
      onRefresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setEnriching(false);
    }
  }

  return (
    <div className="rounded-xl border border-line/80 bg-parchment-raised p-4 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-sm font-semibold text-ink-900">
              {prospect.full_name || "Name not confirmed"}
            </span>
            <ConfidenceBadge confidence={prospect.confidence} />
          </div>
          {prospect.headline && (
            <p className="mt-1 text-xs leading-relaxed text-ink-600">{prospect.headline}</p>
          )}
          {prospect.current_company && (
            <p className="mt-1 text-[11px] text-ink-500">
              Likely at <span className="font-medium text-ink-700">{prospect.current_company}</span>
              <span className="ml-1 italic">(best guess)</span>
            </p>
          )}
          {prospect.location_text && (
            <p className="mt-1 flex items-center gap-1 text-[11px] text-ink-500">
              <MapPin size={10} /> {prospect.location_text}
            </p>
          )}
        </div>
        {prospect.linkedin_url && (
          <a
            href={prospect.linkedin_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-line bg-parchment text-ink-600 hover:border-ink-500 hover:text-ink-900"
            title="Open LinkedIn"
          >
            <LinkedinIcon size={15} />
          </a>
        )}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {prospect.enrichment_status === "ENRICHED" && prospect.email && (
          <span className="flex items-center gap-1.5 rounded-lg bg-good-100 px-2.5 py-1.5 text-xs font-medium text-good-700">
            <Mail size={12} /> {prospect.email}
          </span>
        )}
        {prospect.enrichment_status === "ENRICHED" && prospect.phone && (
          <span className="flex items-center gap-1.5 rounded-lg bg-good-100 px-2.5 py-1.5 text-xs font-medium text-good-700">
            <Phone size={12} /> {prospect.phone}
          </span>
        )}
        {prospect.enrichment_status === "DISCOVERED" && (
          <button
            onClick={enrich}
            disabled={enriching}
            className="rounded-lg bg-ink-900 px-3 py-1.5 text-xs font-semibold text-parchment-raised hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {enriching ? "Looking…" : "Find contact info"}
          </button>
        )}
        {prospect.enrichment_status === "NO_CONTACT_FOUND" && (
          <span className="text-xs text-ink-500">No email/phone found yet</span>
        )}
        {error && <span className="text-xs text-alert-600">{error}</span>}
      </div>
    </div>
  );
}

function SearchForm({ onSearched }) {
  const [criteriaText, setCriteriaText] = useState("");
  const [roleKeywords, setRoleKeywords] = useState("");
  const [location, setLocation] = useState("");
  const [extraKeywords, setExtraKeywords] = useState("");
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState(null);

  const inputClass =
    "w-full rounded-xl border border-line bg-parchment-raised px-3 py-2.5 text-sm text-ink-900 placeholder:text-ink-500/60 focus:border-gold-500 focus:outline-none focus:ring-2 focus:ring-gold-100";

  async function submit(e) {
    e.preventDefault();
    setSearching(true);
    setError(null);
    try {
      const res = await api.searchProspects({
        criteria_text: criteriaText,
        role_keywords: roleKeywords.split(",").map((s) => s.trim()).filter(Boolean),
        location: location.trim() || null,
        extra_keywords: extraKeywords.split(",").map((s) => s.trim()).filter(Boolean),
      });
      onSearched(res);
    } catch (err) {
      setError(err.message.replace(/^\d+\s*/, ""));
    } finally {
      setSearching(false);
    }
  }

  return (
    <form
      onSubmit={submit}
      className="overflow-hidden rounded-2xl border border-line bg-gradient-to-br from-parchment-raised via-parchment to-[#e8ecf2] shadow-sm"
    >
      <div className="border-b border-line/70 bg-parchment-raised/80 px-4 py-3 sm:px-5">
        <div className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-ink-900 text-parchment-raised">
            <Search size={15} />
          </span>
          <div>
            <p className="text-sm font-semibold text-ink-900">Start a new search</p>
            <p className="text-[11px] text-ink-500">Describe who you want — we’ll look up real LinkedIn profiles.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3.5 p-4 sm:grid-cols-2 sm:p-5">
        <div className="sm:col-span-2">
          <label className="mb-1.5 block text-xs font-semibold text-ink-800">
            Name this search
          </label>
          <input
            value={criteriaText}
            onChange={(e) => setCriteriaText(e.target.value)}
            placeholder="e.g. AI developer in Canada"
            required
            className={inputClass}
          />
          <p className="mt-1 text-[11px] text-ink-500">Just for you — so you can find this search later.</p>
        </div>
        <div>
          <label className="mb-1.5 block text-xs font-semibold text-ink-800">
            Job titles or skills
          </label>
          <input
            value={roleKeywords}
            onChange={(e) => setRoleKeywords(e.target.value)}
            placeholder="AI Developer, Machine Learning"
            required
            className={inputClass}
          />
          <p className="mt-1 text-[11px] text-ink-500">Separate with commas if more than one.</p>
        </div>
        <div>
          <label className="mb-1.5 block text-xs font-semibold text-ink-800">Where</label>
          <input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Canada, Mehsana, Remote…"
            className={inputClass}
          />
        </div>
        <div className="sm:col-span-2">
          <label className="mb-1.5 block text-xs font-semibold text-ink-800">
            Extra details <span className="font-normal text-ink-500">(optional)</span>
          </label>
          <input
            value={extraKeywords}
            onChange={(e) => setExtraKeywords(e.target.value)}
            placeholder='e.g. 3+ years, fintech, "open to work"'
            className={inputClass}
          />
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 border-t border-line/70 bg-parchment-raised/60 px-4 py-3 sm:px-5">
        <button
          type="submit"
          disabled={searching}
          className="flex items-center gap-2 rounded-xl bg-ink-900 px-4 py-2.5 text-sm font-semibold text-parchment-raised shadow-md shadow-ink-900/20 hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Search size={15} /> {searching ? "Searching…" : "Search people"}
        </button>
        {error && <span className="text-xs text-alert-600">{error}</span>}
      </div>
    </form>
  );
}

function SearchGroupCard({
  search,
  prospects,
  expanded,
  onToggle,
  onRefreshProspect,
}) {
  const peopleCount = prospects.length;
  const foundLabel = search.result_count != null ? search.result_count : peopleCount;

  return (
    <div
      className={`overflow-hidden rounded-2xl border bg-parchment-raised shadow-sm transition-shadow ${
        expanded ? "border-ink-900/20 shadow-md" : "border-line hover:shadow-md"
      }`}
    >
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-start gap-3 px-4 py-4 text-left sm:px-5"
      >
        <span
          className={`mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${
            expanded ? "bg-ink-900 text-parchment-raised" : "bg-[#eef2f8] text-ink-700"
          }`}
        >
          <Users size={18} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-display text-base font-semibold leading-snug text-ink-900">
              {search.criteria_text || "Untitled search"}
            </h3>
            <span className="mt-0.5 shrink-0 text-ink-500">
              {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </span>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-ink-900/5 px-2.5 py-1 text-[11px] font-semibold text-ink-800">
              {peopleCount} {peopleCount === 1 ? "person" : "people"} here
            </span>
            {foundLabel !== peopleCount && (
              <span className="rounded-full bg-parchment px-2.5 py-1 text-[11px] text-ink-500">
                {foundLabel} matched online
              </span>
            )}
            {search.location && (
              <span className="inline-flex items-center gap-1 rounded-full bg-parchment px-2.5 py-1 text-[11px] text-ink-600">
                <MapPin size={10} /> {search.location}
              </span>
            )}
            <span className="rounded-full bg-parchment px-2.5 py-1 text-[11px] text-ink-500">
              {formatWhen(search.created_at)}
            </span>
            {typeof search.spend === "number" && (
              <span className="rounded-full bg-gold-100/80 px-2.5 py-1 text-[11px] font-medium text-gold-700">
                Cost {search.spend.toFixed(2)}
              </span>
            )}
          </div>
          {(search.role_keywords || "").trim() && (
            <p className="mt-2 truncate text-[11px] text-ink-500">
              Looking for: {search.role_keywords}
            </p>
          )}
          <p className="mt-1.5 text-[11px] font-medium text-ink-600">
            {expanded ? "Hide people" : "Open to see people from this search"}
          </p>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-line bg-[#f7f5f0]/60 px-4 py-4 sm:px-5">
          {peopleCount === 0 ? (
            <div className="rounded-xl border border-dashed border-line bg-parchment-raised px-4 py-8 text-center">
              <Users className="mx-auto text-ink-400" size={24} />
              <p className="mt-2 text-sm text-ink-600">No new people saved for this search.</p>
              <p className="mt-1 text-xs text-ink-500">
                They may already be in an earlier search (we don’t add the same LinkedIn twice).
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {prospects.map((p) => (
                <ProspectCard key={p.id} prospect={p} onRefresh={onRefreshProspect} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ProspectFinder() {
  const [prospects, setProspects] = useState(null);
  const [searches, setSearches] = useState(null);
  const [error, setError] = useState(null);
  const [openSearchId, setOpenSearchId] = useState(null);
  const [didAutoOpen, setDidAutoOpen] = useState(false);

  function refreshProspects() {
    api.listProspects().then(setProspects).catch((err) => setError(err.message));
  }

  function refreshSearches() {
    api.listProspectSearches().then(setSearches).catch((err) => setError(err.message));
  }

  useEffect(() => {
    refreshProspects();
    refreshSearches();
  }, []);

  // Open the newest search once on first load — don't re-open if the user collapses it.
  useEffect(() => {
    if (didAutoOpen || !searches?.length) return;
    setOpenSearchId(searches[0].id);
    setDidAutoOpen(true);
  }, [searches, didAutoOpen]);

  function handleSearched(res) {
    setProspects((prev) => {
      const existingIds = new Set((prev || []).map((p) => p.id));
      const fresh = (res.prospects || []).filter((p) => !existingIds.has(p.id));
      return [...fresh, ...(prev || [])];
    });
    if (res.search?.id) {
      setSearches((prev) => {
        const rest = (prev || []).filter((s) => s.id !== res.search.id);
        return [res.search, ...rest];
      });
      setOpenSearchId(res.search.id);
    } else {
      refreshSearches();
    }
  }

  const prospectsBySearch = useMemo(() => {
    const map = new Map();
    for (const p of prospects || []) {
      const key = p.search_id || "_unknown";
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(p);
    }
    return map;
  }, [prospects]);

  const totalSpend = (searches || []).reduce((sum, s) => sum + (s.spend || 0), 0);
  const totalPeople = prospects?.length ?? 0;

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-5 px-6 py-6">
      <div className="overflow-hidden rounded-2xl border border-line bg-gradient-to-br from-parchment-raised via-parchment to-[#e8ecf2] px-5 py-5 shadow-sm sm:px-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-gold-700">
              <Sparkles size={12} /> People search
            </p>
            <h1 className="mt-1 font-display text-2xl font-semibold text-ink-900">
              Prospect Finder
            </h1>
            <p className="mt-1.5 max-w-2xl text-sm leading-relaxed text-ink-600">
              Find real people on LinkedIn by role and place. Each search becomes its own folder —
              open one to see everyone from that search. These people stay here; they don’t enter
              your leads pipeline.
            </p>
          </div>
          {(searches?.length > 0 || totalPeople > 0) && (
            <div className="flex flex-wrap gap-2">
              <span className="rounded-xl border border-line bg-parchment-raised px-3 py-2 text-center">
                <p className="text-[10px] font-semibold uppercase tracking-wide text-ink-500">Searches</p>
                <p className="text-lg font-semibold text-ink-900">{searches?.length || 0}</p>
              </span>
              <span className="rounded-xl border border-line bg-parchment-raised px-3 py-2 text-center">
                <p className="text-[10px] font-semibold uppercase tracking-wide text-ink-500">People</p>
                <p className="text-lg font-semibold text-ink-900">{totalPeople}</p>
              </span>
              <span className="rounded-xl border border-line bg-parchment-raised px-3 py-2 text-center">
                <p className="text-[10px] font-semibold uppercase tracking-wide text-ink-500">Spent</p>
                <p className="text-lg font-semibold text-ink-900">{totalSpend.toFixed(2)}</p>
              </span>
            </div>
          )}
        </div>
      </div>

      <SearchForm onSearched={handleSearched} />

      {error && (
        <p className="rounded-xl border border-alert-600/30 bg-alert-100 px-4 py-3 text-sm text-alert-700">
          {error}
        </p>
      )}

      <div>
        <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="font-display text-lg font-semibold text-ink-900">Your searches</h2>
            <p className="mt-0.5 text-xs text-ink-500">
              Tap a search to open its people. One search = one group.
            </p>
          </div>
        </div>

        {!searches && <p className="text-xs text-ink-500">Loading your searches…</p>}

        {searches && searches.length === 0 && (
          <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-line bg-parchment-raised py-14 text-center">
            <Users className="text-ink-400" size={32} />
            <p className="text-sm font-medium text-ink-700">No searches yet</p>
            <p className="max-w-sm text-xs text-ink-500">
              Use the form above. When results come back, they’ll appear here as a card you can open anytime.
            </p>
          </div>
        )}

        {searches && searches.length > 0 && (
          <div className="flex flex-col gap-3">
            {searches.map((s) => (
              <SearchGroupCard
                key={s.id}
                search={s}
                prospects={prospectsBySearch.get(s.id) || []}
                expanded={openSearchId === s.id}
                onToggle={() => setOpenSearchId((id) => (id === s.id ? null : s.id))}
                onRefreshProspect={refreshProspects}
              />
            ))}
          </div>
        )}

        {/* Rare: people whose search row is gone — keep them findable */}
        {prospects && (prospectsBySearch.get("_unknown") || []).length > 0 && (
          <div className="mt-3">
            <SearchGroupCard
              search={{
                id: "_unknown",
                criteria_text: "Other saved people",
                result_count: prospectsBySearch.get("_unknown").length,
                spend: null,
                created_at: null,
              }}
              prospects={prospectsBySearch.get("_unknown")}
              expanded={openSearchId === "_unknown"}
              onToggle={() => setOpenSearchId((id) => (id === "_unknown" ? null : "_unknown"))}
              onRefreshProspect={refreshProspects}
            />
          </div>
        )}
      </div>
    </div>
  );
}
