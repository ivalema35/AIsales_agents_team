import { useState } from "react";
import { Check, Mail, MessageCircle, X as XIcon } from "lucide-react";
import { api } from "../api/client";
import { useConfirm } from "../lib/ConfirmContext";
import Badge from "./ui/Badge";

// 2026-09-10, real user ask: approving a campaign sends its real first-touch EMAIL and
// WhatsApp message to an admin test contact instead of a real lead (services/
// campaign_service.send_test_outreach_preview) -- real outreach to this campaign's
// actual leads stays blocked, per channel, until approved here (or via the matching
// one-click link in that test email -- same effect, either path).
function ChannelRow({ icon: Icon, label, testSent, approvedAt, testError, onApprove, onReject, busy }) {
  const approved = !!approvedAt;
  return (
    <div className="flex flex-wrap items-center gap-2 py-2">
      <Icon size={13} className="text-ink-500" />
      <span className="text-xs font-semibold text-ink-900">{label}</span>
      {approved ? (
        <Badge variant="SUCCESS">Approved — live</Badge>
      ) : testSent ? (
        <Badge variant="WARNING">Test sent, pending approval</Badge>
      ) : (
        <Badge variant="NEUTRAL">Not tested yet</Badge>
      )}
      {testError && (
        <span className="text-[11px] text-alert-600" title={testError}>Test send failed</span>
      )}
      <div className="ml-auto flex items-center gap-1.5">
        {!approved ? (
          <button
            onClick={onApprove}
            disabled={busy}
            className="flex items-center gap-1 rounded-md bg-ink-900 px-2.5 py-1.5 text-[11px] font-medium text-parchment-raised hover:opacity-90 disabled:opacity-50"
          >
            <Check size={11} /> Approve real {label}
          </button>
        ) : (
          <button
            onClick={onReject}
            disabled={busy}
            className="flex items-center gap-1 rounded-md px-2.5 py-1.5 text-[11px] font-medium text-alert-600 hover:bg-alert-100 disabled:opacity-50"
          >
            <XIcon size={11} /> Pause real sends
          </button>
        )}
      </div>
    </div>
  );
}

export default function OutreachApprovalCard({ campaign, onUpdated }) {
  const [busyChannel, setBusyChannel] = useState(null);
  const [error, setError] = useState(null);
  const confirm = useConfirm();

  const testResult = campaign.test_outreach_result || {};

  async function setApproval(channel, approved) {
    const ok = await confirm(
      approved
        ? {
            title: `Approve real ${channel === "EMAIL" ? "EMAIL" : "WhatsApp"} outreach for "${campaign.name}"?`,
            message:
              "Real leads in this campaign will start receiving real messages on this channel. " +
              "Make sure the test message you received looked right first.",
            confirmLabel: "Approve",
          }
        : {
            title: `Pause real ${channel === "EMAIL" ? "EMAIL" : "WhatsApp"} outreach for "${campaign.name}"?`,
            message: "Real sends on this channel stop immediately. You can re-approve any time.",
            confirmLabel: "Pause",
          }
    );
    if (!ok) return;

    setBusyChannel(channel);
    setError(null);
    try {
      const updated = await api.setCampaignOutreachApproval(campaign.id, channel, approved);
      onUpdated(updated);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyChannel(null);
    }
  }

  return (
    <div className="rounded-lg border border-line bg-parchment-raised p-3.5">
      <h3 className="text-xs font-semibold text-ink-900">Real outreach approval</h3>
      <p className="mt-0.5 text-[11px] leading-relaxed text-ink-500">
        The real first-touch email and WhatsApp message this campaign would send went to your
        own test contact. Approve each channel here (or click the link in the test email) to
        let real leads in this campaign start receiving it.
      </p>
      {error && <p className="mt-1.5 rounded bg-alert-100 px-2 py-1.5 text-[11px] text-alert-600">{error}</p>}
      <div className="mt-1 divide-y divide-line">
        <ChannelRow
          icon={Mail}
          label="EMAIL"
          testSent={!!campaign.test_outreach_sent_at}
          approvedAt={campaign.email_outreach_approved_at}
          testError={testResult.email?.error}
          busy={busyChannel === "EMAIL"}
          onApprove={() => setApproval("EMAIL", true)}
          onReject={() => setApproval("EMAIL", false)}
        />
        <ChannelRow
          icon={MessageCircle}
          label="WHATSAPP"
          testSent={!!campaign.test_outreach_sent_at}
          approvedAt={campaign.whatsapp_outreach_approved_at}
          testError={testResult.whatsapp?.error}
          busy={busyChannel === "WHATSAPP"}
          onApprove={() => setApproval("WHATSAPP", true)}
          onReject={() => setApproval("WHATSAPP", false)}
        />
      </div>
    </div>
  );
}
