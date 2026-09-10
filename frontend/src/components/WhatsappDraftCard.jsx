import { useState } from "react";
import { AlertTriangle, Boxes, Check, Sparkles, Tag, X as XIcon } from "lucide-react";
import { api } from "../api/client";
import { useConfirm } from "../lib/ConfirmContext";
import Badge from "./ui/Badge";

// 2026-09-09, real user ask: an AI-drafted WhatsApp template needs to be reviewable,
// feedback-able, and approvable from EITHER the WhatsApp Templates page's own "AI
// Proposed" tab OR a specific campaign's own Daily Review (DailyReviewPanel.jsx) --
// "yaha ana na pade" (no need to come here [to the separate page]). Self-contained, same
// pattern as TodoItemCard.jsx: owns its own item/error/busy state, `onResolved(id)` tells
// whichever parent list is rendering it to drop the card once approved/rejected. A
// revision updates the card in place -- no removal, no parent involvement needed.
//
// `qc_caution` is shown as its own distinct warning (separate from the AI's own
// `reasoning`) for a draft saved despite QC raising a concern -- see propose_new_template's
// `guarantee` mode: nothing here ever reaches Meta without this same Approve click
// regardless, so the human decides with full information rather than the concern silently
// withholding the draft.
export default function WhatsappDraftCard({ item: initialItem, onResolved }) {
  const [t, setT] = useState(initialItem);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [instruction, setInstruction] = useState("");
  const [withButton, setWithButton] = useState(!!t.button_url);
  const [revising, setRevising] = useState(false);
  const confirm = useConfirm();

  async function approve() {
    const ok = await confirm({
      title: "Approve and submit this AI-drafted template to Meta?",
      message:
        "This sends a real Create Template request to your WhatsApp Business Account. " +
        "It cannot be edited once submitted, and repeated bad submissions can affect your " +
        "account's standing with Meta. Review the wording above carefully before approving.",
      confirmLabel: "Approve & Submit to Meta",
    });
    if (!ok) return;

    setBusy(true);
    setError(null);
    try {
      await api.approveWhatsappTemplate(t.id);
      onResolved(t.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function reject() {
    const ok = await confirm({
      title: "Reject this AI-drafted template?",
      message: "It will never be sent to Meta and this can't be undone. The AI can always propose another.",
      confirmLabel: "Reject",
    });
    if (!ok) return;

    setBusy(true);
    setError(null);
    try {
      await api.rejectWhatsappTemplate(t.id);
      onResolved(t.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function submitFeedback() {
    if (!instruction.trim()) return;
    setRevising(true);
    setError(null);
    try {
      const updated = await api.reviseWhatsappTemplate(t.id, instruction.trim(), withButton);
      setT(updated);
      setInstruction("");
      setShowFeedback(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setRevising(false);
    }
  }

  return (
    <div className="rounded-md border border-gold-100 bg-gold-100/40 p-3">
      <div className="flex flex-wrap items-center gap-1.5">
        <Sparkles size={12} className="text-gold-500" />
        <span className="text-xs font-semibold text-ink-900">{t.name}</span>
        <Badge variant="NEUTRAL">{t.purpose}{t.followup_level ? ` L${t.followup_level}` : ""}</Badge>
        {t.button_url && (
          <span title={t.button_url} className="rounded bg-gold-100 px-1.5 py-0.5 text-[10px] font-medium text-gold-700">
            Button: {t.button_label || "View"}
          </span>
        )}
        {t.button_2_url && (
          <span title={t.button_2_url} className="rounded bg-gold-100 px-1.5 py-0.5 text-[10px] font-medium text-gold-700">
            Button 2: {t.button_2_label || "View"}
          </span>
        )}
        <Badge variant="NEUTRAL">{t.category}</Badge>
        <span className="flex items-center gap-1 font-mono text-[10px] font-medium text-ink-500">
          <Boxes size={10} /> {t.product_title || "Shared -- all products"}
        </span>
      </div>
      <p className="mt-1.5 whitespace-pre-wrap text-[11px] leading-relaxed text-ink-700">
        "{t.body_text}"
      </p>
      {t.variable_labels.length > 0 && (
        <p className="mt-1 flex items-center gap-1 font-mono text-[10px] text-ink-500">
          <Tag size={10} /> {t.variable_labels.join(", ")}
        </p>
      )}
      {t.reasoning && (
        <p className="mt-1.5 rounded bg-parchment-raised/70 px-2 py-1.5 text-[11px] italic leading-relaxed text-ink-500">
          AI's reasoning: {t.reasoning}
        </p>
      )}
      {t.qc_caution && (
        <p className="mt-1.5 flex items-start gap-1.5 rounded bg-warm-100 px-2 py-1.5 text-[11px] leading-relaxed text-warm-700">
          <AlertTriangle size={12} className="mt-0.5 shrink-0" />
          <span>QC flagged a concern (for your review, didn't block this draft): {t.qc_caution}</span>
        </p>
      )}
      {error && <p className="mt-1.5 rounded bg-alert-100 px-2 py-1.5 text-[11px] text-alert-600">{error}</p>}
      <div className="mt-2.5 flex flex-wrap items-center gap-2">
        <button
          onClick={approve}
          disabled={busy}
          className="flex items-center gap-1 rounded-md bg-ink-900 px-2.5 py-1.5 text-[11px] font-medium text-parchment-raised hover:opacity-90 disabled:opacity-50"
        >
          <Check size={11} /> Approve & Submit to Meta
        </button>
        <button
          onClick={() => setShowFeedback((v) => !v)}
          disabled={busy}
          className="rounded-md px-2.5 py-1.5 text-[11px] font-medium text-ink-700 hover:bg-parchment-raised-2 disabled:opacity-50"
        >
          Give feedback
        </button>
        <button
          onClick={reject}
          disabled={busy}
          className="flex items-center gap-1 rounded-md px-2.5 py-1.5 text-[11px] font-medium text-alert-600 hover:bg-alert-100 disabled:opacity-50"
        >
          <XIcon size={11} /> Reject
        </button>
      </div>
      {showFeedback && (
        <div className="mt-2.5 flex flex-col gap-1.5 border-t border-gold-100 pt-2.5">
          <textarea
            rows={2}
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="e.g. Make it shorter, or mention the free trial instead"
            className="w-full resize-none rounded-md border border-line px-2.5 py-1.5 text-[11px] text-ink-900 placeholder:text-ink-500 focus:border-gold-500 focus:outline-none"
          />
          <div className="flex flex-wrap items-center gap-2.5">
            <label className="flex items-center gap-1.5 text-[11px] text-ink-600">
              <input type="checkbox" checked={withButton} onChange={(e) => setWithButton(e.target.checked)} />
              Include a button
            </label>
            <button
              onClick={submitFeedback}
              disabled={revising || !instruction.trim()}
              className="rounded-md bg-gold-600 px-2.5 py-1.5 text-[11px] font-medium text-parchment-raised hover:opacity-90 disabled:opacity-50"
            >
              {revising ? "Revising…" : "Revise draft"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
