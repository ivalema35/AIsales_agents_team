"""The WhatsApp DETAILING REPLY PATH (PROTOTYPE, scratch copy): the instant, fixed-text answer for a lead who taps "yes" (or types a plain yes such as
"haan") after a DETAILING-studio template, plus a hand-off to the owner. No AI anywhere: every word the lead can receive is in detailing_config.json.

Why a separate module (not demo_responder.py): the demo is a real-estate state machine (budget / BHK / visit slot) switched by `demo_mode`, which is already ON for
campaign 1; this path must stay OFF until the owner switches it, must never start the real-estate demo and must not change what campaign-1 leads receive.

Two jobs:
  1. CLAIM. A trusted lead message that belongs to a DETAILING template is "claimed": api/inbound.py then does NOT call demo_responder or sales_agent for it, so the
     real-estate demo and the real-estate AI persona can never answer a detailing studio. "Belongs to" = (a) the tapped message (context id) is a template_sent record of
     a detailing template, or (b) no usable context id and the sender's number is the recipient (decoded from the wamid, the same way sales_agent does) of a recent
     detailing template_sent. Anything else returns False before any write, so campaign 1 is untouched.
  2. ANSWER. Only for a claimed message: STOP words -> suppress (always); "yes" tap / typed plain yes -> hand-off + (mode on) ONE fixed reply per template send;
     "not now" -> log only; anything else (price, questions, voice notes, "send the demo") -> hand-off, no automatic text.

Safety rails: OFF by default (flag `detailing_mode` off|test|on, written ONLY by the owner's own WhatsApp, services/owner_channel.py); STOP ALL silences it; only a webhook
request that passed the secret check is trusted; replies only to someone who wrote first (inside the 24 h window); idempotent by wamid (demo_seen UNIQUE) and once per
template send; caps; suppressed numbers are never answered (except ONE STOP confirmation); any error is logged and swallowed.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from cognition.hard_classifiers import is_autoreply
from database.models import AgentActivity, AgentHandoff, DemoSeen, OwnerInbox
from services import agent_service, demo_responder
from services.whatsapp_message import TEXT_KINDS

logger = logging.getLogger(__name__)

MODE_FLAG = "detailing_mode"          # agent_flags key: off | test | on
MODES = ("off", "test", "on")
CONFIG_PATH = Path(__file__).with_name("detailing_config.json")
NAME_MARK = "detailing"               # any template whose name contains this is ALWAYS claimed, even if the config does not list it yet

CLAIM_DAYS = 60                       # how far back a template send is looked up for the claim
AUTO_REPLY_DAYS = 7                   # an automatic reply goes out only if the template was sent at most this long ago
WINDOW_HOURS = 23                     # WhatsApp's free-reply window is 24 h from the lead's message; a message older than this gets no automatic reply
MAX_AUTO_PER_PHONE_PER_DAY = 2
MAX_AUTO_PER_DAY = 30
MAX_ALERTS_PER_DAY = 20
MEDIA_COOLDOWN_HOURS = 6
MAX_TEXT = 500
MAX_YES_WORDS = 4
TEST_LABELS = ("owner test", "boss test")               # lead_ref labels of our own test sends (engagement_sync.py also has a bare "test " prefix: too broad for a studio called "Test ...")

BANNED = re.compile(r"(?i)\b(price|prices|pricing|free|instant|instantly|every|gets|guarantee|guaranteed)\b|your ads|मुफ़?्त|मुफ्त|फ्री|तुरंत|गारंटी|कीमत")

OWNER_TEXTS = {
    "owner_done": "Test run finished. No hand-off was created and nothing was suppressed.",
    "alert_yes": "DETAILING lead - {name} {what}.\nAutomatic reply: {auto}.\nReply by hand before {deadline} IST (24 h rule): wa.me/{phone}\nNo time was promised to them.",
    "alert_other": "DETAILING lead - {name} wrote (unverified): \"{text}\"\nNo automatic reply was sent.\nReply by hand before {deadline} IST (24 h rule): wa.me/{phone}",
}

_cfg_cache = {"mtime": None, "data": None}


# =====================================================================================================================
# config
# =====================================================================================================================
def _key(text) -> str:
    """Words of a text in one comparable form: NFC, lower-case, Latin + Devanagari + Gujarati letters only, single spaces."""
    return demo_responder._norm(unicodedata.normalize("NFC", demo_responder._apos(text)))


def _validate(data) -> list:
    """Problems that make the config unsafe to use (an empty list = fine). A bad config never raises: the module then only CLAIMS and hands off, it sends nothing."""
    from services import sales_agent                 # lazy: the reply validator and the AI-disclosure pattern of the existing agent
    problems = []
    templates = data.get("templates") if isinstance(data, dict) else None
    if not isinstance(templates, dict) or not templates:
        return ["no templates"]
    for name, tpl in templates.items():
        if not isinstance(tpl, dict):
            problems.append("%s: not an object" % name)
            continue
        for field in ("yes_labels", "notnow_labels"):
            for label in tpl.get(field) or []:
                if not isinstance(label, str) or not label.strip() or len(label) > 25:
                    problems.append("%s: bad %s %r (1-25 characters)" % (name, field, label))
                elif demo_responder.is_trigger("button", label) or demo_responder._is_hard_stop(label):
                    problems.append("%s: %s %r would start the real-estate demo or count as STOP" % (name, field, label))
        if not tpl.get("yes_labels"):
            problems.append("%s: yes_labels is empty" % name)
        texts = tpl.get("texts") or {}
        for tkey in ("yes_reply", "stop_ack", "media_reply"):
            text = texts.get(tkey)
            if text is None and tkey == "media_reply":
                continue
            if not isinstance(text, str) or not text.strip():
                problems.append("%s: texts.%s missing" % (name, tkey))
                continue
            ok, reason, _ = sales_agent.check_reply(text, False)
            if not ok:
                problems.append("%s: texts.%s rejected by the reply validator: %s" % (name, tkey, reason))
            if BANNED.search(text):
                problems.append("%s: texts.%s contains a banned campaign word" % (name, tkey))
            if len(text) > 400:
                problems.append("%s: texts.%s is longer than 400 characters" % (name, tkey))
            if tkey in ("yes_reply", "media_reply") and not (sales_agent._AI_RE.search(text) and re.search(r"STOP", text)):
                problems.append("%s: texts.%s must say it is automatic/AI and carry the word STOP" % (name, tkey))
    return problems


def load_config() -> dict:
    """{"templates": {...}, "valid": bool, "problems": [...]}; re-read only when the file changes (no restart needed after a config update)."""
    try:
        mtime = CONFIG_PATH.stat().st_mtime
    except OSError:
        return {"templates": {}, "valid": False, "problems": ["config file missing"]}
    if _cfg_cache["mtime"] != mtime:
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            problems = _validate(data)
            templates = data.get("templates") if isinstance(data, dict) and isinstance(data.get("templates"), dict) else {}
        except (OSError, ValueError):
            templates, problems = {}, ["config file unreadable"]
        _cfg_cache.update(mtime=mtime, data={"templates": templates, "valid": not problems, "problems": problems})
    return _cfg_cache["data"]


def _is_detailing_name(name, cfg) -> bool:
    name = str(name or "")
    return name in cfg["templates"] or NAME_MARK in name.lower()


# =====================================================================================================================
# small helpers
# =====================================================================================================================
def _now_iso() -> str:
    return agent_service.now_iso()


def _since(hours: float) -> str:
    return agent_service.to_iso(agent_service.utc_now() - timedelta(hours=hours))


def _digits(value) -> str:
    return re.sub(r"\D", "", str(value or ""))


def _ref(phone: str) -> str:
    return "detailing:" + hashlib.sha1(str(phone).encode()).hexdigest()[:10]


def _clip(text, n: int) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "..."


def _safe_text(text, n: int) -> str:
    """Lead text before it goes to the owner or a hand-off: no links, no long digit runs (it cannot carry a clickable link or a payment instruction)."""
    t = unicodedata.normalize("NFKC", str(text or ""))
    t = re.sub(r"(?i)(https?://|www\.)\S+", "[link]", t)
    t = re.sub(r"(?<!\d)(?:\d[\s.\-]?){8,}", "[number]", t)
    return _clip(t, n)


def _phone_from_wamid(wamid) -> str:
    """The wamid Meta returns for a message we sent embeds the recipient's number (base64). Checked on 11 of 11 real template sends of this account."""
    token = str(wamid or "")
    token = token.split(".", 1)[1] if token.startswith("wamid.") else token
    try:
        raw = base64.b64decode(token + "=" * (-len(token) % 4))
    except Exception:  # noqa: BLE001
        return ""
    found = re.search(rb"91\d{10}", raw)
    return found.group(0).decode() if found else ""


def _payload(row) -> dict:
    try:
        data = json.loads(row.payload_json or "{}")
        return data if isinstance(data, dict) else {}
    except ValueError:
        return {}


def _is_test_label(label) -> bool:
    low = str(label or "").strip().lower()
    return any(low.startswith(t) for t in TEST_LABELS)


def _mark(db, key) -> bool:
    """Writes a UNIQUE marker into demo_seen. False = it already existed (a webhook retry, a double tap ...). Written BEFORE anything is sent: at most once."""
    db.add(DemoSeen(wamid=str(key)[:200], ts=_now_iso()))
    try:
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False


def get_mode(db) -> str:
    value, _ = agent_service.get_flag(db, MODE_FLAG)
    return value if value in MODES else "off"


def _event(db, kind, summary, origin=None, phone="", extra=None, direction="in") -> None:
    payload = {"template": (origin or {}).get("template"), "phone": demo_responder._mask(phone)}
    payload.update(extra or {})
    try:
        agent_service.add_event(db, (origin or {}).get("lead_ref") or _ref(phone), "whatsapp", direction, kind, summary, payload)
    except Exception:  # noqa: BLE001
        db.rollback()
        logger.exception("could not write a detailing activity event")


# =====================================================================================================================
# recognising a detailing message (read-only: no write happens before a message is claimed)
# =====================================================================================================================
def _like_escape(token: str) -> str:
    return token.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _origin_by_wamid(db, wamid):
    """The template_sent record whose wamid is exactly `wamid` (the message the lead tapped / replied to), or None."""
    token = re.sub(r"[^A-Za-z0-9._=-]", "", str(wamid or ""))[:120]
    if not token:
        return None
    pattern = '%"' + _like_escape(token) + '"%'
    rows = (db.query(AgentActivity).filter(AgentActivity.kind == "template_sent", AgentActivity.ts >= _since(CLAIM_DAYS * 24),
                                           AgentActivity.payload_json.like(pattern, escape="\\")).order_by(AgentActivity.id.desc()).limit(5).all())
    for row in rows:
        p = _payload(row)
        if p.get("wamid") == token:                       # exact match (a LIKE wildcard can never pick a wrong row)
            return {"template": str(p.get("template") or ""), "wamid": token, "lead_ref": row.lead_ref, "ts": row.ts, "observation": p.get("project")}
    return None


def _origin_by_number(db, phone, cfg):
    """The newest detailing template_sent whose recipient (decoded from the wamid) is `phone`, or None."""
    patterns = ["%" + NAME_MARK + "%"] + ['%"' + _like_escape(n) + '"%' for n in cfg["templates"] if NAME_MARK not in n.lower()]
    rows = (db.query(AgentActivity).filter(AgentActivity.kind == "template_sent", AgentActivity.ts >= _since(CLAIM_DAYS * 24),
                                           or_(*[AgentActivity.payload_json.like(p, escape="\\") for p in patterns]))
            .order_by(AgentActivity.id.desc()).limit(200).all())
    for row in rows:
        p = _payload(row)
        if _is_detailing_name(p.get("template"), cfg) and _phone_from_wamid(p.get("wamid")) == phone:
            return {"template": str(p.get("template") or ""), "wamid": str(p.get("wamid")), "lead_ref": row.lead_ref, "ts": row.ts, "observation": p.get("project")}
    return None


def _recognise(db, msg, phone, cfg):
    """None = not a detailing message (the caller returns False and the old flow runs untouched)."""
    ctx = (msg.get("context") or {}).get("id")
    if ctx:
        origin = _origin_by_wamid(db, ctx)
        if origin is not None:
            if not _is_detailing_name(origin["template"], cfg):
                return None                               # the lead answered one of the campaign-1 templates: not ours
            origin["via"] = "context"
            return origin
    origin = _origin_by_number(db, phone, cfg)
    if origin is None:
        return None
    if demo_responder._active_session(db, phone) is not None:
        return None                                       # a demo that started before this claim existed may finish
    origin["via"] = "number"
    return origin


# =====================================================================================================================
# classifying what the lead did
# =====================================================================================================================
def _is_yes_text(key: str, typed: str, tpl: dict) -> bool:
    words = key.split()
    vocab = {_key(w) for w in tpl.get("yes_words") or []}
    return bool(tpl.get("typed_yes", True)) and 1 <= len(words) <= MAX_YES_WORDS and "?" not in typed and not re.search(r"\d", key) and all(w in vocab for w in words)


def _is_decline_text(key: str, tpl: dict) -> bool:
    return key in {_key(w) for w in tpl.get("decline_words") or []}


def _classify(kind: str, typed: str, tpl: dict) -> str:
    """ignore | stop | yes | notnow | media | other"""
    if kind in ("reaction", "sticker"):
        return "ignore"
    if typed and demo_responder._is_hard_stop(typed):
        return "stop"
    if kind not in TEXT_KINDS:
        return "media"                                    # voice note, image, document, location ... (only the caption was looked at for STOP)
    if typed and is_autoreply(typed):
        return "ignore"                                   # another business's auto-responder: never answer a robot
    if demo_responder._only_noise(typed):
        return "ignore"
    key = _key(typed)
    if kind in ("button", "interactive"):
        if key in {_key(x) for x in tpl.get("yes_labels") or []}:
            return "yes"
        if key in {_key(x) for x in tpl.get("notnow_labels") or []}:
            return "notnow"
        return "other"
    if _is_yes_text(key, typed, tpl):
        return "yes"
    if _is_decline_text(key, tpl):
        return "notnow"
    return "other"


# =====================================================================================================================
# the answer
# =====================================================================================================================
def _auto_allowed(db, phone) -> tuple:
    if agent_service.is_paused(db):
        return False, "STOP ALL (paused)"
    mode = get_mode(db)
    if mode == "off":
        return False, "automatic reply is OFF"
    if mode == "test" and phone not in demo_responder._test_numbers():
        return False, "test mode and this number is not a test number"
    if not demo_responder._credentials_ok():
        return False, "WhatsApp credentials missing"
    return True, ""


def _msg_age_ok(msg) -> bool:
    try:
        sent = datetime.fromtimestamp(int(msg.get("timestamp")), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return True                                       # no usable timestamp: the webhook just delivered it, treat it as fresh
    return agent_service.utc_now() - sent <= timedelta(hours=WINDOW_HOURS)


def _template_age_ok(origin) -> bool:
    try:
        return agent_service.utc_now() - agent_service.parse_iso(origin["ts"]) <= timedelta(days=AUTO_REPLY_DAYS)
    except Exception:  # noqa: BLE001
        return False


def _human_replied_since(db, origin, phone) -> bool:
    """wa.py reply logs a `reply_sent` activity (lead label, or the masked number when --lead was left out): a person already took over."""
    refs = {r for r in (origin.get("lead_ref"), demo_responder._mask(phone)) if r}
    return db.query(AgentActivity.id).filter(AgentActivity.kind == "reply_sent", AgentActivity.lead_ref.in_(refs), AgentActivity.ts >= origin["ts"]).first() is not None


def _caps_ok(db, phone) -> bool:
    day = db.query(func.count(AgentActivity.id)).filter(AgentActivity.kind == "detailing_auto_reply", AgentActivity.ts >= _since(24)).scalar() or 0
    mine = db.query(func.count(AgentActivity.id)).filter(AgentActivity.kind == "detailing_auto_reply", AgentActivity.ts >= _since(24),
                                                         AgentActivity.payload_json.like('%"' + demo_responder._mask(phone) + '"%')).scalar() or 0
    return day < MAX_AUTO_PER_DAY and mine < MAX_AUTO_PER_PHONE_PER_DAY


def _handoff(db, origin, phone, reason, brief, priority="high") -> None:
    """Hand-off row + CRM to-do first (so a failed send can never hide the lead); one open hand-off per number per 24 h, later messages are appended."""
    try:
        existing = db.query(AgentHandoff).filter(AgentHandoff.contact == "+" + phone, AgentHandoff.status == "open", AgentHandoff.ts >= _since(24)).first()
        if existing is None:
            agent_service.create_handoff(db, _ref(phone), "%s (detailing)" % (origin.get("lead_ref") or "unnamed"), "+" + phone, reason, brief, priority)
        else:
            existing.brief = _clip((existing.brief or "") + " || NEW (%s): %s" % (_now_iso()[:16], brief), 1500)
            if priority == "high":
                existing.priority = "high"
            db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()
        logger.exception("detailing: could not write the hand-off")


def _alerts_today(db) -> int:
    return db.query(func.count(AgentActivity.id)).filter(AgentActivity.kind == "detailing_alert", AgentActivity.ts >= _since(24)).scalar() or 0


def _alert(db, origin, phone, text) -> None:
    """A WhatsApp note to the owner, ONLY inside his own 24 h window (free). Otherwise the hand-off card and the operator lane are the signal."""
    try:
        from services import owner_channel
        owners = sorted(owner_channel.owner_numbers())
        within = bool(agent_service.owner_last_seen(db).get("within_24h"))
        if not owners or not within or agent_service.is_paused(db) or _alerts_today(db) >= MAX_ALERTS_PER_DAY:
            return                                          # STOP ALL means nothing is WhatsApped, the owner included
        demo_responder._send_text(owners[0], text[:900])
        _event(db, "detailing_alert", "owner alerted", origin, phone, direction="out")
    except Exception:  # noqa: BLE001
        db.rollback()
        logger.exception("detailing: owner alert failed")


def _send(db, phone, text) -> tuple:
    try:
        return True, demo_responder._send_text(phone, text)
    except Exception as exc:  # noqa: BLE001
        logger.warning("detailing: the automatic reply could not be sent (%s)", type(exc).__name__)
        return False, type(exc).__name__


def _deadline(msg) -> str:
    try:
        sent = datetime.fromtimestamp(int(msg.get("timestamp")), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        sent = agent_service.utc_now()
    return (sent + timedelta(hours=24)).astimezone(demo_responder.IST).strftime("%H:%M")


def _handle_lead(db, msg, kind, origin, cfg, phone) -> None:
    wamid = msg.get("id")
    tpl = cfg["templates"].get(origin["template"]) or {}
    _kind, typed = demo_responder._typed_text(msg)
    typed = demo_responder._apos(typed)[:MAX_TEXT]
    cls = _classify(_kind, typed, tpl)
    if cls == "ignore" or not wamid:
        return
    if not _mark(db, "det:" + str(wamid)):
        return                                            # webhook retry
    texts = tpl.get("texts") or {}
    use_texts = bool(cfg["valid"])
    suppressed = demo_responder._suppressed(db, phone)
    test_send = _is_test_label(origin.get("lead_ref"))
    name = origin.get("lead_ref") or "unnamed"
    _event(db, "detailing_inbound", "Detailing lead %s: %s" % (cls, _clip(typed, 60) or "[%s]" % _kind), origin, phone,
           {"class": cls, "via": origin.get("via"), "kind": _kind, "mode": get_mode(db)})

    if cls == "stop":
        demo_responder._suppress(db, phone)               # always, whatever the mode
        db.query(AgentHandoff).filter(AgentHandoff.contact == "+" + phone, AgentHandoff.status == "open").update({"status": "cancelled"}, synchronize_session=False)
        db.commit()
        ok, _why = _auto_allowed(db, phone)
        if ok and use_texts and texts.get("stop_ack") and _mark(db, "detstop:" + phone):
            _send(db, phone, texts["stop_ack"])           # ONE confirmation, even though the number is now on the do-not-contact list
        return
    if suppressed:
        _event(db, "detailing_blocked", "suppressed number: no reply, no hand-off", origin, phone)
        return
    if cls == "notnow":
        return

    # yes / other / media: the human signal first
    what = {"yes": "said YES", "other": "wrote something", "media": "sent a voice note / file"}[cls]
    reason = {"yes": "Said YES to the detailing video message", "other": "Wrote after the detailing video message (not a plain yes)",
              "media": "Sent a voice note / image / file after the detailing video message"}[cls]
    brief = "Template %s sent %s. %s: %s. Their observation line: %s" % (origin["template"], (origin.get("ts") or "")[:16], what, _safe_text(typed, 240) or "[%s]" % _kind,
                                                                       _safe_text(origin.get("observation"), 160))
    if not test_send:
        _handoff(db, origin, phone, reason, brief, "high" if cls == "yes" else "normal")

    sent, status = False, "not sent"
    ok, why = _auto_allowed(db, phone)
    reply_key = "yes_reply" if cls == "yes" else ("media_reply" if cls == "media" else None)
    if reply_key and not ok:
        status = "not sent (%s)" % why
    elif reply_key:
        text = texts.get(reply_key)
        if not use_texts or not text:
            status = "not sent (config invalid or text missing)"
        elif not _msg_age_ok(msg):
            status = "not sent (the lead's message is older than the 24 h window)"
        elif cls == "yes" and not _template_age_ok(origin):
            status = "not sent (the template is older than %d days)" % AUTO_REPLY_DAYS
        elif cls == "yes" and _human_replied_since(db, origin, phone):
            status = "not sent (a person already replied)"
        elif not _caps_ok(db, phone):
            status = "not sent (daily cap)"
        else:
            bucket = origin["wamid"] if cls == "yes" else "%s:%d" % (phone, int(agent_service.utc_now().timestamp() // (MEDIA_COOLDOWN_HOURS * 3600)))
            if not _mark(db, ("detsend:" if cls == "yes" else "detmedia:") + bucket):
                status = "not sent (already answered once)"
            elif demo_responder._suppressed(db, phone):
                status = "not sent (suppressed)"
            else:
                sent, detail = _send(db, phone, text)
                status = "sent" if sent else "FAILED (%s)" % detail
                _event(db, "detailing_auto_reply" if sent else "detailing_reply_failed", "automatic reply %s" % status, origin, phone,
                       {"template_wamid": origin["wamid"], "key": reply_key}, direction="out")
    if not test_send:
        if cls == "yes":
            _alert(db, origin, phone, OWNER_TEXTS["alert_yes"].format(name=name, what=what, auto=status, deadline=_deadline(msg), phone=phone))
        else:
            _alert(db, origin, phone, OWNER_TEXTS["alert_other"].format(name=name, text=_safe_text(typed, 160) or "[%s]" % _kind, deadline=_deadline(msg), phone=phone))


# =====================================================================================================================
# entry points called from api/inbound.py
# =====================================================================================================================
def maybe_handle_lead_message(db, msg: dict, sender: str, kind: str, text: str, trusted: bool) -> bool:
    """A lead's WhatsApp message, AFTER the normal inbound handling (feed row, STOP suppression). True = it belongs to a detailing template and was handled here: the caller
    must NOT pass it to the real-estate demo or the AI agent. False = not ours (nothing was written). Never raises."""
    claimed = False
    try:
        if not trusted:
            return False
        phone = _digits(msg.get("from"))
        if not phone:
            return False
        cfg = load_config()
        origin = _recognise(db, msg, phone, cfg)
        if origin is None:
            return False
        claimed = True
        _handle_lead(db, msg, kind, origin, cfg, phone)
    except Exception:  # noqa: BLE001
        db.rollback()
        logger.exception("detailing responder failed (ignored; a recognised message stays claimed)")
    return claimed


def status_text(db) -> str:
    cfg = load_config()
    since = _since(24)
    inbound = db.query(func.count(AgentActivity.id)).filter(AgentActivity.kind == "detailing_inbound", AgentActivity.ts >= since).scalar() or 0
    autos = db.query(func.count(AgentActivity.id)).filter(AgentActivity.kind == "detailing_auto_reply", AgentActivity.ts >= since).scalar() or 0
    sends = db.query(func.count(AgentActivity.id)).filter(AgentActivity.kind == "template_sent", AgentActivity.ts >= since, AgentActivity.payload_json.like("%" + NAME_MARK + "%")).scalar() or 0
    rows = (db.query(AgentActivity).filter(AgentActivity.kind == "template_sent", AgentActivity.payload_json.like("%" + NAME_MARK + "%")).order_by(AgentActivity.id.desc()).limit(10).all())
    decodable = sum(1 for r in rows if _phone_from_wamid(_payload(r).get("wamid")))
    notes = []
    if agent_service.is_paused(db):
        notes.append("PAUSED by STOP ALL: nothing is sent until RESUME.")
    if not demo_responder._credentials_ok():
        notes.append("WhatsApp credentials missing.")
    if not cfg["valid"]:
        notes.append("CONFIG PROBLEM: %s. Nothing is sent." % "; ".join(cfg["problems"][:3]))
    return ("Detailing auto-reply: mode %s. Templates in config: %d. Last 24 h: %d detailing sends logged, %d lead messages, %d automatic replies. "
            "Number lookup works on %d of the last %d detailing sends. %s" % (get_mode(db).upper(), len(cfg["templates"]), sends, inbound, autos, decodable, len(rows), " ".join(notes))).strip()


# ---- the owner's own commands (DETAILING ON / OFF / TEST / STATUS / RUN) and the owner testing the tap from his phone ----------------
_RUN_ARG_RE = re.compile(r"^\s*detailing\s+run(?:\s+(.{1,60}?))?\s*[.!]*\s*$", re.IGNORECASE)


def after_owner_message(db, msg: dict, outcome: str) -> None:
    """After the owner's message was stored and any command applied. Confirms mode changes, answers STATUS, runs `DETAILING RUN`, and shows the owner what a lead
    sees when HE taps the yes button of a detailing template. Never raises. Plain chat with the agent is never consumed."""
    try:
        _owner_message(db, msg, outcome)
    except Exception:  # noqa: BLE001
        db.rollback()
        logger.exception("detailing responder (owner path) failed (ignored)")


def _mark_owner_row_processed(db, wamid) -> None:
    db.query(OwnerInbox).filter(OwnerInbox.wamid == wamid, OwnerInbox.processed_at.is_(None)).update({"processed_at": _now_iso()}, synchronize_session=False)
    db.commit()


def _owner_message(db, msg, outcome) -> None:
    if outcome == "duplicate":
        return
    owner = _digits(msg.get("from"))
    wamid = msg.get("id")
    cfg = load_config()
    if outcome in ("detailing-on", "detailing-off", "detailing-test", "detailing-status"):
        _mark_owner_row_processed(db, wamid)
        word = outcome.split("-", 1)[1]
        demo_responder._send_text(owner, ("" if word == "status" else "Detailing auto-reply is now %s. " % word.upper()) + status_text(db))
        return
    if outcome == "detailing-run":
        _mark_owner_row_processed(db, wamid)
        _kind, typed = demo_responder._typed_text(msg)
        match = _RUN_ARG_RE.match(typed or "")
        wanted = (match.group(1) or "").strip() if match else ""
        name = wanted if wanted in cfg["templates"] else next(iter(cfg["templates"]), "")
        text = ((cfg["templates"].get(name) or {}).get("texts") or {}).get("yes_reply")
        if not cfg["valid"] or not text:
            demo_responder._send_text(owner, "Detailing: the config has a problem, so there is nothing to show. " + status_text(db))
            return
        demo_responder._send_text(owner, text)
        demo_responder._send_text(owner, OWNER_TEXTS["owner_done"])
        return
    if outcome != "stored":
        return
    kind, typed = demo_responder._typed_text(msg)
    ctx = (msg.get("context") or {}).get("id")
    if kind not in ("button", "interactive") or not ctx:
        return
    origin = _origin_by_wamid(db, ctx)
    if origin is None or not _is_detailing_name(origin["template"], cfg):
        return
    _mark_owner_row_processed(db, wamid)                  # the agent must not answer this tap as if it were chat
    tpl = cfg["templates"].get(origin["template"]) or {}
    if _classify(kind, demo_responder._apos(typed)[:MAX_TEXT], tpl) == "yes" and cfg["valid"] and _mark(db, "det:" + str(wamid)):
        demo_responder._send_text(owner, (tpl.get("texts") or {}).get("yes_reply"))
        demo_responder._send_text(owner, OWNER_TEXTS["owner_done"])
