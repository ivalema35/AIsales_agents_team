# AI-BOS Dashboard → CRM Upgrade Plan

Working plan for turning the Phase 4.4 dashboard (Kanban + alerts + toggles) into a proper
CRM: full lead visibility, dashboard-editable settings, real analytics, and a deliberately
**improved** UI/UX — not a default-Tailwind CRUD look. This file is the source of truth for
that upgrade; update it the same way `tracker.md` gets updated (mark items done, note real
bugs found, don't rewrite history).

Collaboration protocol stays the same as the rest of the project: explain each phase in
Hinglish before building it, wait for confirmation, build with real data (no mocks unless
truly unavoidable), verify live, then move to the next phase.

---

## 0. Why this exists

The dashboard today (`PipelineKanban`, `LeadCard`, `AlertsPanel`, `SystemToggles`,
`Products.jsx`) is read-mostly and shallow — a lead card shows a score and a justification
line, nothing else. Every richer signal already exists in the database (`agent_events`,
`outreach_logs`, `inbound_conversations`, `lead_review_insights`) but has no UI. Four
operationally-real settings (`EOD_REPORT_RECIPIENTS`, `EOD_REPORT_WHATSAPP_RECIPIENTS`, the
daily send caps, discovery cooldown) are `.env`-only and require a code-level restart to
change. There is no analytics view at all — every "how many X today" question this session
has been answered by a one-off SQL query, not a page.

---

## 1. Design system — the "improved, not basic" rules

Read this section before writing any component in Phases 1–4. A phase is not done just
because the data renders; it's done when it also follows these rules.

### 1.1 Current state (audit, 2026-08-17)
- Palette in use: `slate-*` (neutral/brand), `red-*` (danger/HOT), `amber-*` (warm/warning),
  `emerald-*` (success/on). Reasonable choices, inconsistently applied — border colors vary
  between `slate-100/200/300` with no rule for which situation gets which, shadows are
  `shadow-sm`/none with no rule either.
- Components are single-purpose files with inline Tailwind, no shared design tokens, no
  shared `Badge`/`EmptyState`/`Modal` primitives — `Toggle` in `SystemToggles.jsx` is the
  only reusable pattern so far (and it isn't exported for reuse elsewhere, `Products.jsx`
  had to re-implement its own toggle from scratch — fix this in Phase 1/4, see §5).
- Zero loading/empty/error state design — components either render data or render nothing
  (`if (!settings) return null`). No skeleton states, no "0 leads yet" empty-state copy.
- Logo (`/logo.png`, slate/charcoal "A" mark) is the only brand asset in use.

### 1.2 Design tokens (target — apply from Phase 1 onward)

**Color roles** (semantic, not just "which slate shade looked fine"):
| Role | Token | Used for |
|---|---|---|
| Brand/neutral base | `slate-900` / `slate-800` | Nav, primary buttons, headings |
| Surface | `white` on `slate-50` page background | Cards on page |
| Border (default) | `border-slate-200` | Every card border, always — stop mixing 100/200/300 |
| Border (subtle divider) | `border-slate-100` | Inside a card, section dividers only |
| HOT / danger / destructive | `red-600` text, `red-50` bg, `red-200` ring | Tier=HOT, escalation, dangerous toggles |
| WARM / caution | `amber-600` text, `amber-50` bg, `amber-200` ring | Tier=WARM, pending/needs-review states |
| COLD / muted | `slate-500` text, `slate-100` bg | Tier=COLD, disabled states |
| Success / sent / on | `emerald-600` text, `emerald-50` bg | SENT status, toggle-on state |
| Info / neutral action | `slate-700` | Secondary buttons, links |

Never introduce a new color outside this table without adding it here first — consistency
is the entire point.

**Typography scale** (Tailwind defaults, but pick ONE per role and stop mixing):
- Page title: `text-lg font-semibold text-slate-900`
- Card title / lead name: `text-sm font-medium text-slate-900`
- Body / description: `text-sm text-slate-600`
- Meta / timestamp / label: `text-xs text-slate-500` (or `text-slate-400` for the least
  important tier — e.g. a timestamp that's genuinely secondary to everything around it)
- Never use a font size not in `{xs, sm, base, lg, xl}` — no arbitrary `text-[13px]`.

**Spacing**: card padding is always `p-4` (dense list rows may use `p-3`, never smaller).
Gaps between stacked elements: `gap-2` within a tight cluster (badge row), `gap-3`/`gap-4`
between distinct sections of a card, `gap-6` between page sections. Pick from `{2,3,4,6}`,
nothing else, so rhythm stays consistent across pages built in different phases.

**Elevation**: cards get `shadow-sm` + `ring-1 ring-slate-200`, nothing heavier (this is a
dense data app, not a marketing page — heavy shadows read as noisy). Modals/overlays get
`shadow-xl` to separate from the page behind them. Never use `shadow-md`/`shadow-lg` on an
inline card — reserve visual weight for things that are actually elevated above the page.

**Shared primitives to build once, reuse everywhere** (Phase 1 creates these under
`frontend/src/components/ui/`, every later phase imports them instead of re-implementing):
- `Badge` — tier/status/channel pills (replaces the ad-hoc `TIER_STYLES` object duplicated
  per-component today).
- `Toggle` — extract from `SystemToggles.jsx`, make it the ONE toggle implementation.
- `Modal` / `SlideOver` — for the Lead Detail view (§3) and any future detail view.
- `EmptyState` — icon + one-line message + optional action, for every "0 results" case.
- `Skeleton` — loading placeholder for the async fetches this app is full of.
- `StatTile` — for Phase 3's analytics cards (see `dataviz` skill's stat-tile guidance
  when this gets built — Claude: load the `dataviz` skill before writing any chart or
  stat-tile code in Phase 3, don't hand-roll chart color choices).

**Interaction rules**:
- Every clickable surface has a visible `hover:` state and, where it's a real button/link
  (not a decorative card), a focus ring (`focus:outline-none focus:ring-2
  focus:ring-slate-400`) — this app has zero keyboard-accessible focus states today, fix
  it as each component gets touched, don't do a separate a11y pass at the end.
  Real symptom that motivated this rule: `DiscoveryToggle` and the Kanban card's own click
  handler are both currently only mouse-operable.
- Transitions stay under 200ms and only apply to color/opacity/transform — never animate
  layout-affecting properties (`height`, `width`) without `overflow-hidden` guarding it,
  the earlier toggle-knob bug this session was exactly a "the visual state didn't reliably
  reflect real state" class of bug and animation is where that risk concentrates.
- Empty and error states are DESIGNED, not `{error && <p>...</p>}` bolted on — every list
  view needs a real empty-state (icon + copy), every fetch needs a real loading skeleton,
  not a blank screen while `useState(null)` is falsy.

**Responsiveness**: this is an internal admin tool, desktop-first is fine, but the layout
must not visually break below ~1280px (a laptop screen) — test at that width before calling
a phase done, don't assume a giant monitor.

---

## 2. Phase-wise plan

### Phase 1 — Lead Detail Modal/Page
**Goal**: click any lead anywhere in the app → see everything the system knows about it in
one place, real data, real timeline, editable.

**Backend**
- `GET /api/v1/leads/<id>/timeline` — merges `agent_events`, `outreach_logs`,
  `inbound_conversations`, and lead status-change history into one chronologically sorted
  list, each entry tagged with a type (`DISCOVERED`, `SCORED`, `OUTREACH_SENT`,
  `REPLY_RECEIVED`, `ESCALATED`, ...) the frontend can map to an icon/color.
- `GET /api/v1/leads/<id>` extended (or a new `/full` variant) to include: full contact
  info, `LeadFirmographics` if present, `LeadReviewInsight` (pain points with evidence
  quotes), `LeadScore` (full breakdown, not just the summary line already on `LeadCard`).
- `PATCH /api/v1/leads/<id>` extended for manual admin overrides (status, contact fields) —
  reuse the existing PATCH route if one exists, check `api/leads.py` first rather than
  assuming a new endpoint is needed.

**Frontend**
- `LeadDetailModal` (or a routed page, `/leads/:id` — routed page is usually better for a
  CRM since it's bookmarkable/shareable and back-button works correctly; prefer this over
  a modal unless there's a concrete reason not to) using the `Modal`/`SlideOver` primitive
  from §1.2.
- Sections: header (name, tier badge, status badge, region), contact info (editable),
  score breakdown (icp_fit/pain_match/reachability/buying_signal, justification), pain
  points (code + evidence quote + severity, from `LeadReviewInsight`), full timeline
  (chronological, icon per event type), sent/received messages (real email/WhatsApp
  bodies, not just metadata), edit form for manual overrides.
- Wire every existing lead-showing surface (`LeadCard`, `AlertsPanel` rows) to open this
  view on click, replacing/alongside the existing inline "Send Outreach Now" button.

**DoD for this phase**: open a real lead with real history (e.g. GameZone Visnagar) → every
section shows real data, no placeholder/lorem text; edit a field → persists and reflects on
the Kanban card too; timeline order is verifiably correct against the DB's own timestamps
(spot-check at least one lead by comparing the UI against a direct SQL query, the same
verify-don't-trust discipline as the rest of this project).

### Phase 2 — Settings expansion (dashboard-editable, no restart)
**Goal**: every operationally-relevant setting that's currently `.env`-only becomes
dashboard-editable and takes effect without a process restart.

**Backend**
- Migrate `EOD_REPORT_RECIPIENTS`, `EOD_REPORT_WHATSAPP_RECIPIENTS`, and any other
  operationally-tweaked-often value (daily send caps, discovery cooldown hours) from
  `Config` (`.env`, read once at process start) into `system_settings` (DB-backed, checked
  fresh every tick — the exact pattern `discovery_enabled`/`auto_reply_enabled` already
  use). Keep `Config`'s `.env` value as the fallback default for a fresh install, same as
  `get_bool(db, KEY, default=...)` already does for the boolean switches — this needs a
  string/list-valued equivalent (`get_json`/`get_list` in `services/system_settings.py`).
- Extend `api/settings.py`'s known-keys set accordingly.

**Frontend**
- Extend `SystemToggles.jsx` (or split into a dedicated `SettingsPanel.jsx` if it's getting
  crowded — likely the right call once there are 8+ settings, not just 4 booleans) with
  editable text/list inputs for recipients, numeric inputs for caps/cooldowns.

**DoD**: change a recipient in the dashboard → next EOD trigger (manual `POST
/reports/generate` for the live test) actually sends to the new address, zero code/`.env`
edit, zero restart.

### Phase 3 — Analytics / Charts
**Goal**: pipeline funnel, channel performance, time trend, per-product breakdown — real
data, properly designed charts (not default chart-library styling).

**Before writing any chart code here: load the `dataviz` skill.** It defines the palette
formula, chart-type heuristics, and accessibility rules this phase must follow — don't
improvise colors or chart types.

**Backend**
- `GET /api/v1/analytics/funnel` — count per `Lead.status` (or a fixed funnel stage
  ordering), optionally filtered by product/date range.
- `GET /api/v1/analytics/channel-performance` — per channel: sent, replied, reply rate,
  high-intent rate (reuses the same aggregation logic `reporting_service.py` already has
  for a single day — generalize `_collect_metrics()`'s channel logic into a reusable
  function both the EOD report AND this endpoint call, don't duplicate the query).
- `GET /api/v1/analytics/trend?granularity=day|week|month` — leads discovered / outreach
  sent / replies received, bucketed over time.
- `GET /api/v1/analytics/by-product` — per-product lead counts by status/tier.

**Frontend**
- New `Analytics.jsx` page, added to nav. Funnel (bar or funnel chart), channel performance
  (grouped bars or a small comparison table + sparkline), trend (line chart, granularity
  toggle), per-product (table or grouped bars) — use `StatTile` for headline numbers above
  the charts (total leads, total outreach, overall reply rate).

**DoD**: every chart's numbers independently cross-checked against a direct SQL query for
at least one real day (the project's standing discipline — a chart that LOOKS right isn't
verified right until it's checked against ground truth once).

### Phase 4 — Global UI/UX polish pass

**Goal**: sweep every existing component (`PipelineKanban`, `LeadCard`, `AlertsPanel`,
`Products.jsx`, `SystemToggles.jsx`) to actually use the §1.2 shared primitives and token
rules, not just the new Phase 1–3 surfaces. This phase existing is itself an admission that
Phases 1–3 will inevitably drift from the ruleset under real deadline pressure — budget for
this cleanup explicitly rather than pretending it won't be needed.

- Replace every ad-hoc `TIER_STYLES`-style object with the shared `Badge`.
- Replace `Products.jsx`'s bespoke `DiscoveryToggle` re-implementation with the shared
  `Toggle` extracted in Phase 1.
- Add real empty/loading states everywhere still missing one.
- Full keyboard-navigation pass (tab through the whole app once, everything reachable).
- Verify at 1280px width per §1.2's responsiveness rule.

---

## 2A. Add-on UI phases (5–9) — added 2026-08-19

Phases 1–4 above turned the dashboard into a CRM that can **see** the system's data. Phases 5–9
are the UI half of `MASTER_DEVELOPMENT_PRD.md` §5A (backend Phases 6–10): surfaces that let the
operator **steer** the system without a code change, and finally see it running live.

Each phase here pairs 1:1 with its backend phase and **must not start before that backend phase's
DoD gate is green** — a UI built against an unfinished API is the fastest way to ship a screen full
of plausible-looking placeholder numbers, which this project has explicitly refused to do since
Phase 3's analytics work.

§1.2's design tokens and §1's "improved, not basic" rules apply to every phase below without
exception. Two additions specific to this block:

- **Live surfaces must distinguish "no data" from "not loaded" from "down".** A monitor page that
  renders an empty feed identically to a dead backend is worse than no monitor page — it manufactures
  false confidence, which is the exact failure Phase 5 exists to fix.
- **Every AI-authored artifact shown to the operator must be visibly labelled as AI-authored** (drafts,
  generated templates, selected subject lines). The operator approving something must always know
  whether a human or the system wrote it.

### Phase 5 — Live System Monitor  *(backend Phase 6)*

**Goal**: answer *"is the system alive, and what is it doing right now?"* on one screen. This is the
direct fix for the operator's own observation — *"abhi crm me ye pata nahi chal raha he ki system kya
kar raha he"* — and for two real incidents that were only ever visible over SSH.

- New `/system` route: per-process liveness cards (`jobs.worker`, `scraper_worker.async_runner`,
  `jobs.discovery_scheduler`, `jobs.inbound_poller`) with real last-seen timestamps — never a static
  green dot.
- Job-queue board: counts by status × type, with `DEAD`/pile-up states visually distinct from healthy.
- Live activity feed from `agent_events` — what was discovered, enriched, scored, sent, just now.
- Stuck-state banner: leads parked in `OUTREACHING`, stale processes, `DEAD` job accumulation.
- Polling on an interval, not WebSocket (same "refuse unneeded infrastructure" call as dropping n8n).
- A compact liveness indicator in the global nav, so the answer is visible from every page.

**DoD**: kill a real background process → the page reflects `DOWN` within the staleness window and
recovers on restart; the feed's contents match a direct SQL query of `agent_events`; a deliberately
stuck lead is visibly flagged while a mid-send lead is not.

### Phase 6 — Product Targeting & Person-Level Contacts  *(backend Phase 7)*

**Goal**: let the operator define *who* to target, and show every real human found at a lead.

- `Products.jsx`: two new optional multi-value fields — target business categories, target person roles
  (e.g. "Property Manager", "CEO", "Sales Manager"). Both must read clearly as **optional**; a product
  with neither set must look and behave exactly as it does today.
- `LeadDetail.jsx`: a real contacts section — multiple people per lead with role, seniority, decision-maker
  flag, LinkedIn/email/phone, and **the source of each** (scraped / Hunter / LinkedIn lookup).
- Show contact confidence honestly. A low-confidence guess must not render identically to a verified
  contact — this is the UI half of the backend's "zero wrong-company attachments" gate.
- Backfill progress surface for the one-off social-profile enrichment run (Step 7.7), including its
  estimated API spend **before** the operator starts it, not after.

**DoD**: a product saved with no targeting fields round-trips unchanged; a real lead with multiple
Hunter contacts renders all of them with correct roles and sources.

### Phase 7 — Message Format Builder & Content Library  *(backend Phase 8)*

**Goal**: the highest-leverage screen in this whole block — where the operator shapes what every
outreach message says, without touching code. Directly serves the stated goal of raising open/read rates.

- **Format builder**: an ordered, editable list of slots (greeting/hook → this business's own weak
  points → solution → demo link → CTA), per product and channel, with a global default. The operator
  writes *structure and intent*, never final copy — the UI must make that distinction obvious, since
  it is the entire concept of the feature.
- **Live preview against a real lead**: pick an existing lead, see what the format actually produces.
  Without this the operator is editing blind, and format quality is unmeasurable until a real send.
- **Content library**: demo URLs, video links, case studies, testimonials — per product, taggable, with
  an active/inactive toggle. This is what the AI selects from; it must be obvious that an asset absent
  here can never appear in a message.
- Format versioning visible, since a format change resets the performance history Phase 8 measures.

**DoD**: two different formats produce visibly different previews for the same real lead; a
product-scoped asset never appears in another product's preview.

### Phase 8 — Performance, Follow-ups & Template Manager  *(backend Phase 9)*

**Goal**: close the loop visually — what worked, what is scheduled next, and what the AI wants to change.

- **Variant performance**: sent / seen / replied per format version, subject line and template, built on
  the real Seen tracking already shipped in Phase 3 of this plan. Follow the `dataviz` skill as that
  phase did — validate the palette with the script, never eyeball it.
- **Never fabricate a metric.** Where no real signal exists the cell reads `—`, exactly as the EOD
  report's KPI section already does for `spam_rate`.
- **Follow-up timeline** per lead: which touches were sent, which is scheduled next, why the sequence
  ended (replied / opted out / exhausted). An opted-out lead must be unmistakable.
- **Template manager**: submit a WhatsApp template from the CRM, watch its real Meta approval state
  (`PENDING`/`APPROVED`/`REJECTED` + rejection reason), activate an approved one — all without a code edit.
- **AI-proposed template review queue**: the human approval gate for the ⭐ autonomous template loop.
  Clearly labelled AI-authored, showing the performance evidence that triggered the proposal, with
  approve/reject as a deliberate action — never a default-approve.

**DoD**: performance numbers reconcile against a direct SQL query for one real day; a real template
submitted here reaches Meta and its real state appears without a code change.

### Phase 9 — Channel Manager & Social Draft Queue  *(backend Phase 10)*

**Goal**: make channel policy and its hard limits legible — including the things the system
deliberately will not do.

- **Channel policy per region**: which channels are allowed/preferred where, why a lead was routed the
  way it was. Must state plainly when a region has no policy configured, since that means email-only.
- **Social draft queue** (LinkedIn / Instagram / Facebook): AI-drafted messages a human reviews, copies,
  sends manually, and marks sent. The UI must make clear this is **deliberately manual** — the platforms
  do not permit automated cold sending, and the system contains no code path that could.
- **Voice calling controls** (when Step 10.4 lands): its own kill-switch, visibly separate from and
  stricter than the global outreach switch; per-lead consent basis shown before any call is possible.
- Kill-switch states for every channel visible in one place. Given this project's history — a real WARM
  lead was one tick away from an unauthorised send before the kill-switch existed — a switch whose state
  is ambiguous in the UI is a safety defect, not a polish item.

**DoD**: a Canadian lead visibly routes away from WhatsApp under policy; the social queue can draft and
mark-sent; with the voice switch off, no UI path can initiate a call.

---

## 3. Sequencing note

Phases run in order (1 → 2 → 3 → 4), matching the collaboration protocol already used for
Phases 1–5 of the backend build: explain the phase in Hinglish, confirm, build, verify live
with real data, update this file's checkboxes, move on. Don't start Phase 2 with Phase 1
still partially real/partially placeholder.

- [x] Phase 1 — Lead Detail Modal/Page (built as a routed page `/leads/:id`, 2026-08-17 -- see tracker.md and memory.md for the full build + the international-phone bug this phase surfaced)
- [x] Phase 2 — Settings expansion (2026-08-17 -- EOD recipients + daily send caps + discovery cooldown all moved from .env-only Config to dashboard-editable system_settings, verified live via real PATCH/GET round-trips; see tracker.md)
- [x] Phase 2b — Dedicated Settings page + full .env visibility (2026-08-17, at the user's request) -- new `/settings` route covers every remaining Config value (LLM provider, Resend, WhatsApp, discovery scheduler, inbound email, data-acquisition API keys) with a hint tooltip per field. Secrets are write-only and masked (never sent back to the browser) -- see tracker.md for the full security design. Redesigned same day into a sticky sidebar-nav + 2-column category grid at full page width (matches CRM_UI_UX_PLAN.md §1.2's responsiveness rule) after the initial single-column `max-w-4xl` version wasted most of a wide screen and made a long page of categories tedious to scan. Split "System controls" and "Operational settings" into two visually distinct cards (were one card, distinguished only by a heading). **Real bug found and fixed**: secret fields used `type="password"`, which made browsers treat them as login-form fields and auto-inject an unrelated saved credential -- that injection doesn't fire a normal input event, so the visibly-shown text silently didn't match the field's real (React) value, and copying it did nothing. Switched to `type="text"` with `autoComplete="off"` + password-manager ignore attributes (`data-lpignore`, `data-1p-ignore`) -- there was never a real masking need anyway, since these fields are always empty by default (secrets are write-only).
- [x] Phase 3 — Analytics / Charts (2026-08-17, extended same day with `frontend/src/lib/statusColors.js` -- one fixed color per lead status, shared across Kanban/LeadDetail/Analytics; also fixed a real short-bar-renders-as-a-circle bug, see memory.md) -- new `/analytics` page: pipeline funnel, channel performance, trend line chart, per-product table. Backend aggregations verified against real data before building the frontend. Followed the `dataviz` skill throughout -- validated the categorical palette with its script (not eyeballed), added a table-view fallback for the one series (aqua/replies) the validator flagged below 3:1 contrast on the light surface (its own "relief rule"). See tracker.md for the full build.
  - **Further extended 2026-08-17/18** (still Phase 3 scope, not a new phase): by-product view rebuilt as per-product tier donuts; IST-timezone trend-bucketing bug found and fixed; a whole new real "Seen" tracking pipeline built for both channels from scratch (`api/webhooks.py`, WhatsApp status-webhook handling, `OutreachLog.provider_message_id`/`read_at`); and a new "Sent, seen & replied" chart went through 3 rejected designs before landing on a per-channel donut with mutually-exclusive Replied/Seen-no-reply/Not-seen buckets (the 3 attempts and why each was wrong are in tracker.md and memory.md in full — worth reading before proposing a 4th chart design for anything adjacent to this one, since the pattern of rejection was consistently about FORM, not data).
- [ ] Phase 4 — Global UI/UX polish pass

**Add-on phases (§2A, added 2026-08-19).** Same protocol, one extra rule: each pairs 1:1 with a backend
phase in `MASTER_DEVELOPMENT_PRD.md` §5A and does not start until that backend phase's DoD gate is green.

- [ ] Phase 5 — Live System Monitor *(backend Phase 6)*
- [ ] Phase 6 — Product Targeting & Person-Level Contacts *(backend Phase 7)*
- [ ] Phase 7 — Message Format Builder & Content Library *(backend Phase 8)*
- [ ] Phase 8 — Performance, Follow-ups & Template Manager *(backend Phase 9)*
- [ ] Phase 9 — Channel Manager & Social Draft Queue *(backend Phase 10)*

Phase 4 (polish) is deliberately **not** a prerequisite for Phases 5–9 — it is a sweep over existing
surfaces and can run whenever there's a natural gap. But it should not be skipped indefinitely either:
each new phase adds surfaces that will themselves need it, so the longer it waits the larger it gets.
