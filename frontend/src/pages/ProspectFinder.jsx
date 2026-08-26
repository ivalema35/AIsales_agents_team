import { useEffect, useState } from "react";
import { Search, Users, Mail, Phone, CheckCircle2, AlertCircle, Clock } from "lucide-react";
import { api } from "../api/client";
import { LinkedinIcon } from "../lib/socialIcons";

// Phase 15 Step 15(B) -- standalone, criteria-driven person search, deliberately separate
// from the company-first Leads funnel: a prospect never went through discovery/scoring/
// ICP matching (Table 30 `prospects`, never a row in `leads`), so it gets its own page
// rather than being squeezed into Leads.

// Same two-tier honesty rule as LeadDetail.jsx's own ConfidenceBadge (Phase 15(A).2): a
// low-confidence guess must never render like a verified contact. This search has no
// company-name cross-check the way role-scoped LinkedIn search does (Phase 15(A)), so its
// own confidence values run lower (0.4/0.7 vs 0.5/0.85) -- the badge threshold matches
// that real difference, not a copy-pasted number.
function ConfidenceBadge({ confidence }) {
  if (confidence == null) return null;
  const pct = Math.round(confidence * 100);
  const strong = confidence >= 0.6;
  return (
    <span
      title={strong ? "A cleanly parsed LinkedIn result" : "A weaker keyword match -- verify before relying on this"}
      className={`inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-medium ${
        strong ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
      }`}
    >
      {strong ? <CheckCircle2 size={10} /> : <AlertCircle size={10} />}
      {pct}% {strong ? "likely" : "unverified"}
    </span>
  );
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
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-sm font-semibold text-slate-800">
              {prospect.full_name || "Name not confirmed"}
            </span>
            <ConfidenceBadge confidence={prospect.confidence} />
          </div>
          {prospect.headline && <p className="mt-0.5 text-xs text-slate-500">{prospect.headline}</p>}
          {prospect.current_company && (
            <p className="mt-0.5 text-[11px] text-slate-400">
              at {prospect.current_company}
              <span className="ml-1 italic">(best-effort guess, not verified)</span>
            </p>
          )}
        </div>
        {prospect.linkedin_url && (
          <a
            href={prospect.linkedin_url}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 text-slate-400 hover:text-slate-700"
            title="Open LinkedIn profile"
          >
            <LinkedinIcon size={16} />
          </a>
        )}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {prospect.enrichment_status === "ENRICHED" && prospect.email && (
          <span className="flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-1 text-xs text-emerald-700">
            <Mail size={12} /> {prospect.email}
          </span>
        )}
        {prospect.enrichment_status === "ENRICHED" && prospect.phone && (
          <span className="flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-1 text-xs text-emerald-700">
            <Phone size={12} /> {prospect.phone}
          </span>
        )}
        {prospect.enrichment_status === "DISCOVERED" && (
          <button
            onClick={enrich}
            disabled={enriching}
            className="rounded-md border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {enriching ? "Looking…" : "Find contact info"}
          </button>
        )}
        {prospect.enrichment_status === "NO_CONTACT_FOUND" && (
          <span className="text-xs text-slate-400">No real contact info found</span>
        )}
        {error && <span className="text-xs text-red-600">{error}</span>}
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
      // A 402 budget refusal comes through with a real, specific message -- show it
      // as-is rather than a generic "search failed".
      setError(err.message.replace(/^\d+\s*/, ""));
    } finally {
      setSearching(false);
    }
  }

  return (
    <form onSubmit={submit} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label className="mb-1 block text-xs font-medium text-slate-600">
            What are you looking for? (your own label for this search)
          </label>
          <input
            value={criteriaText}
            onChange={(e) => setCriteriaText(e.target.value)}
            placeholder="e.g. AI developer in Mehsana, 3 years experience"
            required
            className="w-full rounded-md border border-slate-200 px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">
            Role / skill keywords (comma-separated)
          </label>
          <input
            value={roleKeywords}
            onChange={(e) => setRoleKeywords(e.target.value)}
            placeholder="AI Developer, Machine Learning Engineer"
            required
            className="w-full rounded-md border border-slate-200 px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Location</label>
          <input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Mehsana"
            className="w-full rounded-md border border-slate-200 px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
        </div>
        <div className="sm:col-span-2">
          <label className="mb-1 block text-xs font-medium text-slate-600">
            Extra keywords (optional, comma-separated -- e.g. "3+ years")
          </label>
          <input
            value={extraKeywords}
            onChange={(e) => setExtraKeywords(e.target.value)}
            placeholder="3+ years"
            className="w-full rounded-md border border-slate-200 px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
        </div>
      </div>
      <div className="mt-3 flex items-center gap-3">
        <button
          type="submit"
          disabled={searching}
          className="flex items-center gap-1.5 rounded-md bg-slate-800 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Search size={13} /> {searching ? "Searching…" : "Search"}
        </button>
        {error && <span className="text-xs text-red-600">{error}</span>}
      </div>
    </form>
  );
}

function SearchHistory({ searches }) {
  if (!searches || searches.length === 0) return null;
  const totalSpend = searches.reduce((sum, s) => sum + (s.spend || 0), 0);
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="flex items-center gap-1.5 text-sm font-semibold text-slate-800">
          <Clock size={14} className="text-slate-400" /> Search history
        </h3>
        <span className="text-xs text-slate-400">Total spend: {totalSpend.toFixed(2)}</span>
      </div>
      <div className="flex flex-col gap-1.5">
        {searches.slice(0, 10).map((s) => (
          <div key={s.id} className="flex items-center justify-between text-xs">
            <span className="text-slate-600">{s.criteria_text}</span>
            <span className="text-slate-400">
              {s.result_count} found · {s.spend.toFixed(2)} spent · {s.created_at}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ProspectFinder() {
  const [prospects, setProspects] = useState(null);
  const [searches, setSearches] = useState(null);
  const [error, setError] = useState(null);

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

  function handleSearched(res) {
    setProspects((prev) => {
      const existingIds = new Set((prev || []).map((p) => p.id));
      const fresh = res.prospects.filter((p) => !existingIds.has(p.id));
      return [...fresh, ...(prev || [])];
    });
    refreshSearches();
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-5 px-6 py-6">
      <div>
        <h1 className="text-lg font-semibold text-slate-900">Prospect Finder</h1>
        <p className="mt-1 text-xs text-slate-500">
          Search for real people by role/skill/location, independent of the leads funnel --
          these never become leads or affect any funnel metric. Real LinkedIn search results
          only (Serper X-Ray) -- no synthetic or invented profiles. Set a monthly budget under
          Settings before your first search; a search that would exceed it is refused outright.
        </p>
      </div>

      <SearchForm onSearched={handleSearched} />

      {error && <p className="text-sm text-red-600">{error}</p>}

      <SearchHistory searches={searches} />

      <div>
        <h2 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-slate-800">
          <Users size={14} className="text-slate-400" /> Prospects found
          {prospects && <span className="text-slate-400">({prospects.length})</span>}
        </h2>
        {!prospects && <p className="text-xs text-slate-400">Loading…</p>}
        {prospects && prospects.length === 0 && (
          <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-slate-300 bg-white py-12 text-center">
            <Users className="text-slate-300" size={28} />
            <p className="text-sm text-slate-400">No prospects yet -- run a search above.</p>
          </div>
        )}
        {prospects && prospects.length > 0 && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {prospects.map((p) => (
              <ProspectCard key={p.id} prospect={p} onRefresh={refreshProspects} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
