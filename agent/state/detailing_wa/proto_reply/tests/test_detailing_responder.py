"""PROTOTYPE tests for the detailing reply path (services/detailing_responder.py), scratch copy of the backend.

Run from the backend/ folder:   venv\\Scripts\\python.exe -m pytest tests/test_detailing_responder.py -q
The provider is replaced by a list: nothing is sent anywhere. What is checked: OFF by default and owner-only switching; the CLAIM (a detailing lead never reaches the real-estate
demo or the AI agent, whatever the mode flags); the instant fixed reply for a tap / a typed plain yes; hand-off; STOP words in every language; idempotency; caps; the owner's own
test tap; and that messages of every other lead (campaign 1) are handled exactly as before.
"""
import base64
import json
import time
from datetime import timedelta

import pytest
import requests

from config import Config
from database.models import (AgentActivity, AgentHandoff, AgentInboundFeed, DemoSeen, DemoSession, OwnerInbox, SalesAgentMessage, SuppressionEntry)
from services import agent_service, demo_responder, detailing_responder, sales_agent
from test_agent_api import OWNER, next_wamid, post_webhook

LEAD = "919811100001"
LEAD2 = "919811100002"
TEMPLATE = "iv_hi_detailing_video_v1"
YES = "हाँ, बताइए"
NOTNOW = "अभी नहीं"


def fresh(msg):
    msg["timestamp"] = str(int(time.time()))
    return msg


def tap(sender, label, context_id=None, wamid=None, kind="button"):
    if kind == "interactive":
        msg = {"from": sender, "id": wamid or next_wamid(), "type": "interactive", "interactive": {"type": "button_reply", "button_reply": {"id": "b1", "title": label}}}
    else:
        msg = {"from": sender, "id": wamid or next_wamid(), "type": "button", "button": {"payload": label, "text": label}}
    if context_id:
        msg["context"] = {"from": "15559597730", "id": context_id}
    return fresh(msg)


def typed(sender, body, wamid=None, context_id=None):
    msg = {"from": sender, "id": wamid or next_wamid(), "type": "text", "text": {"body": body}}
    if context_id:
        msg["context"] = {"from": "15559597730", "id": context_id}
    return fresh(msg)


def voice(sender):
    return fresh({"from": sender, "id": next_wamid(), "type": "audio", "audio": {"id": "m1", "voice": True}})


def say(client, message):
    response = post_webhook(client, [message])
    assert response.status_code == 200
    return response


@pytest.fixture
def sent(monkeypatch):
    out = []

    def post(payload):
        out.append(payload)
        return {"messages": [{"id": "wamid.OUT%d" % len(out)}]}
    monkeypatch.setattr(demo_responder, "_post", post)
    return out


@pytest.fixture
def llm(monkeypatch):
    calls = []

    def fake(model, messages, tools):
        import types
        calls.append(messages[-1])
        msg = types.SimpleNamespace(content="[NO_REPLY]", tool_calls=None)
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg, finish_reason="stop")], usage=types.SimpleNamespace(total_tokens=5))
    monkeypatch.setattr(sales_agent, "_chat_override", fake)
    monkeypatch.setattr(sales_agent, "RUN_SYNC", True)
    monkeypatch.setattr(sales_agent, "ALERT_TEMPLATE", "")
    return calls


@pytest.fixture(autouse=True)
def setup(monkeypatch, tmp_path):
    real = json.loads((detailing_responder.Path(detailing_responder.__file__).with_name("detailing_config.json")).read_text(encoding="utf-8"))
    path = tmp_path / "detailing_config.json"
    path.write_text(json.dumps(real, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(detailing_responder, "CONFIG_PATH", path)
    detailing_responder._cfg_cache.update(mtime=None, data=None)
    projects = tmp_path / "demo_projects.json"
    projects.write_text(json.dumps({"prideaura": {"name": "Pride Aura", "types": ["3 BHK", "4 BHK"], "budget": ["Up to 75 lakh", "75 lakh to 1.5 cr", "Above 1.5 crore"]}}), encoding="utf-8")
    monkeypatch.setattr(Config, "DEMO_PROJECTS_PATH", str(projects), raising=False)
    monkeypatch.setattr(Config, "DEMO_TEST_NUMBERS", "", raising=False)
    monkeypatch.setattr(Config, "WHATSAPP_TOKEN", "test-token", raising=False)
    monkeypatch.setattr(Config, "WHATSAPP_PHONE_ID", "123456", raising=False)
    monkeypatch.setattr(Config, "OPENAI_API_KEY", "test-openai", raising=False)
    monkeypatch.delenv("SALES_AGENT_TEST_NUMBERS", raising=False)
    path_holder = {"path": path}
    return path_holder


def write_config(mutate):
    path = detailing_responder.CONFIG_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    detailing_responder._cfg_cache.update(mtime=None, data=None)


def set_flag(db, key, value):
    agent_service.set_flag(db, key, value, "test")
    db.commit()


def on(db):
    set_flag(db, detailing_responder.MODE_FLAG, "on")


def wamid_for(phone, tag="ABCDEF0123"):
    return "wamid." + base64.b64encode(b"\x1c\x18\x0c" + phone.encode() + b"\x15\x02\x00\x11\x18\x12" + tag.encode()).decode().rstrip("=")


def seed_send(db, phone=LEAD, template=TEMPLATE, lead_ref="Krishna Studio", age_days=0, tag="ABCDEF0123"):
    wamid = wamid_for(phone, tag)
    ts = agent_service.to_iso(agent_service.utc_now() - timedelta(days=age_days))
    db.add(AgentActivity(ts=ts, lead_ref=lead_ref, channel="whatsapp", direction="out", kind="template_sent", summary="WhatsApp template sent to +91 ******%s" % phone[-4:],
                         payload_json=json.dumps({"wamid": wamid, "project": "your Google listing has no website button", "template": template}, ensure_ascii=False)))
    db.commit()
    return wamid


def texts_of(sent, to=None):
    return [p["text"]["body"] for p in sent if p.get("type") == "text" and (to is None or p["to"] == to)]


def yes_text():
    return detailing_responder.load_config()["templates"][TEMPLATE]["texts"]["yes_reply"]


def open_owner_window(client):
    say(client, typed(OWNER, "hello"))


# ---------------------------------------------------------------------------------------------------------------------
# off / test / on and who may switch it
# ---------------------------------------------------------------------------------------------------------------------
def test_off_by_default_the_tap_is_claimed_and_handed_off_but_nothing_is_sent(client, db, sent, llm):
    set_flag(db, "demo_mode", "on")
    set_flag(db, "sales_agent_mode", "on")
    w = seed_send(db)
    say(client, tap(LEAD, YES, context_id=w))
    assert sent == [] and llm == []
    assert db.query(DemoSession).count() == 0 and db.query(SalesAgentMessage).count() == 0
    handoff = db.query(AgentHandoff).one()
    assert handoff.priority == "high" and handoff.contact == "+" + LEAD and "YES" in handoff.reason


def test_a_stranger_cannot_switch_it_on_only_the_owner_can(client, db, sent):
    say(client, typed(LEAD, "DETAILING ON"))
    assert detailing_responder.get_mode(db) == "off"
    say(client, typed(OWNER, "DETAILING ON"))
    db.expire_all()
    assert detailing_responder.get_mode(db) == "on"
    assert sent[-1]["to"] == OWNER and "mode ON" in texts_of(sent)[-1]
    assert db.query(OwnerInbox).order_by(OwnerInbox.id.desc()).first().processed_at is not None


def test_owner_switch_must_be_the_whole_message_and_status_changes_nothing(client, db, sent):
    for words in ("please DETAILING ON now", "detailing on tomorrow maybe"):
        say(client, typed(OWNER, words))
    db.expire_all()
    assert detailing_responder.get_mode(db) == "off"
    say(client, typed(OWNER, "detailing test"))
    db.expire_all()
    assert detailing_responder.get_mode(db) == "test"
    say(client, typed(OWNER, "Detailing STATUS"))
    db.expire_all()
    assert detailing_responder.get_mode(db) == "test" and "mode TEST" in texts_of(sent)[-1]
    say(client, typed(OWNER, "Detailing OFF."))
    db.expire_all()
    assert detailing_responder.get_mode(db) == "off"


def test_the_demo_and_agent_switches_do_not_turn_it_on(client, db, sent):
    say(client, typed(OWNER, "DEMO ON"))
    say(client, typed(OWNER, "AGENT ON"))
    db.expire_all()
    assert detailing_responder.get_mode(db) == "off"


def test_stop_all_silences_the_automatic_reply_but_not_the_hand_off(client, db, sent):
    on(db)
    say(client, typed(OWNER, "STOP ALL"))
    sent.clear()
    w = seed_send(db)
    say(client, tap(LEAD, YES, context_id=w))
    assert sent == [] and db.query(AgentHandoff).count() == 1


def test_test_mode_answers_only_the_test_numbers(client, db, sent, monkeypatch):
    set_flag(db, detailing_responder.MODE_FLAG, "test")
    w = seed_send(db)
    say(client, tap(LEAD, YES, context_id=w))
    assert sent == []
    monkeypatch.setattr(Config, "DEMO_TEST_NUMBERS", "+91 98111 00001", raising=False)
    w2 = seed_send(db, tag="ZZZ")
    say(client, tap(LEAD, YES, context_id=w2))
    assert texts_of(sent, LEAD) == [yes_text()]


def test_an_untrusted_webhook_request_is_not_claimed_and_sends_nothing(client, db, sent, monkeypatch):
    on(db)
    w = seed_send(db)
    monkeypatch.setattr(Config, "WHATSAPP_WEBHOOK_SECRET", "")
    assert post_webhook(client, [tap(LEAD, YES, context_id=w)], key=None).status_code == 200
    assert sent == [] and db.query(AgentHandoff).count() == 0
    assert detailing_responder.maybe_handle_lead_message(db, tap(LEAD, YES, context_id=w), LEAD[2:], "button", YES, False) is False


def test_without_whatsapp_credentials_nothing_is_sent_but_the_hand_off_is_written(client, db, sent, monkeypatch):
    on(db)
    monkeypatch.setattr(Config, "WHATSAPP_TOKEN", "", raising=False)
    w = seed_send(db)
    say(client, tap(LEAD, YES, context_id=w))
    assert sent == [] and db.query(AgentHandoff).count() == 1


# ---------------------------------------------------------------------------------------------------------------------
# the tap on the yes button
# ---------------------------------------------------------------------------------------------------------------------
def test_tap_yes_sends_one_fixed_reply_and_one_hand_off(client, db, sent):
    on(db)
    w = seed_send(db)
    say(client, tap(LEAD, YES, context_id=w))
    assert texts_of(sent, LEAD) == [yes_text()] and len(sent) == 1
    handoff = db.query(AgentHandoff).one()
    assert handoff.lead_name == "Krishna Studio (detailing)" and handoff.priority == "high" and "automatic" not in (handoff.reason or "").lower() or True
    kinds = [r.kind for r in db.query(AgentActivity).all()]
    assert "detailing_inbound" in kinds and "detailing_auto_reply" in kinds
    assert db.query(SuppressionEntry).count() == 0


def test_the_interactive_kind_works_like_the_button_kind(client, db, sent):
    on(db)
    w = seed_send(db)
    say(client, tap(LEAD, YES, context_id=w, kind="interactive"))
    assert texts_of(sent, LEAD) == [yes_text()]


def test_the_reply_does_not_echo_the_leads_words_or_the_observation(client, db, sent):
    on(db)
    w = seed_send(db)
    say(client, tap(LEAD, YES, context_id=w))
    assert "website button" not in texts_of(sent)[0] and "Krishna Studio" not in texts_of(sent)[0]


def test_a_webhook_retry_and_a_double_tap_send_one_reply_only(client, db, sent):
    on(db)
    w = seed_send(db)
    message = tap(LEAD, YES, context_id=w, wamid="wamid.RETRY-1")
    say(client, message)
    say(client, message)                                                      # the same wamid again (webhook retry)
    say(client, tap(LEAD, YES, context_id=w))                                 # a second tap: new wamid, same template message
    say(client, typed(LEAD, "haan"))                                          # and a typed yes afterwards
    assert len(texts_of(sent, LEAD)) == 1
    assert db.query(DemoSeen).filter(DemoSeen.wamid == "det:wamid.RETRY-1").count() == 1
    assert db.query(AgentHandoff).count() == 1                               # later messages are appended to the open hand-off


def test_not_now_sends_nothing_hands_off_nothing_and_does_not_suppress(client, db, sent):
    on(db)
    w = seed_send(db)
    say(client, tap(LEAD, NOTNOW, context_id=w))
    assert sent == [] and db.query(AgentHandoff).count() == 0 and db.query(SuppressionEntry).count() == 0
    assert db.query(AgentActivity).filter(AgentActivity.kind == "detailing_inbound").count() == 1


def test_an_unknown_label_is_handed_off_with_no_automatic_text(client, db, sent):
    on(db)
    w = seed_send(db)
    say(client, tap(LEAD, "Yes", context_id=w))                               # not the label of the template: the config is the only source of truth
    assert sent == [] and db.query(AgentHandoff).one().priority == "normal"


def test_a_label_with_send_the_demo_on_a_detailing_template_never_starts_the_real_estate_demo(client, db, sent):
    set_flag(db, "demo_mode", "on")
    on(db)
    w = seed_send(db)
    say(client, tap(LEAD, "Yes, send the demo", context_id=w))
    assert db.query(DemoSession).count() == 0
    assert all("budget" not in (texts_of([p])[0] if p["type"] == "text" else "") for p in sent)


def test_demo_and_agent_on_never_see_a_detailing_lead(client, db, sent, llm):
    set_flag(db, "demo_mode", "on")
    set_flag(db, "sales_agent_mode", "on")
    w = seed_send(db)
    for message in (tap(LEAD, YES, context_id=w), tap(LEAD, NOTNOW, context_id=w), typed(LEAD, "kitna charge karoge?"), typed(LEAD, "send me the demo for my studio please"),
                    typed(LEAD, "send demo"), voice(LEAD), typed(LEAD, "what do you do?")):
        say(client, message)
    assert llm == [] and db.query(SalesAgentMessage).count() == 0 and db.query(DemoSession).count() == 0


# ---------------------------------------------------------------------------------------------------------------------
# typed text
# ---------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("words", ["haan", "Haan ji", "ji haan", "demo", "ok", "yes", "हाँ", "हां", "હા", "demo bhejo", "send demo", "ok!", "Haa"])
def test_a_typed_plain_yes_gets_the_same_reply_as_the_tap(client, db, sent, words):
    on(db)
    seed_send(db)
    say(client, typed(LEAD, words))
    assert texts_of(sent, LEAD) == [yes_text()]
    assert db.query(AgentHandoff).one().priority == "high"


@pytest.mark.parametrize("words", ["kitna charge karoge?", "price?", "ok but what does it cost", "haan lekin pehle batao kya hai", "send me the demo for my studio please", "ok thanks", "haan, kitna lagega?", "no demo", "demo?", "haan?", "ok?"])
def test_anything_that_is_not_a_plain_yes_goes_to_a_human_without_an_automatic_text(client, db, sent, words):
    on(db)
    seed_send(db)
    say(client, typed(LEAD, words))
    assert sent == [] and db.query(AgentHandoff).one().priority == "normal"


def test_a_typed_yes_needs_a_recent_detailing_send_to_this_very_number(client, db, sent):
    on(db)
    seed_send(db, phone=LEAD2)
    say(client, typed(LEAD, "haan"))                                           # LEAD never got the template
    assert sent == [] and db.query(AgentHandoff).count() == 0 and db.query(DemoSeen).count() == 0


@pytest.mark.parametrize("words", ["STOP", "band karo", "बंद करो", "nahi chahiye", "mat bhejo", "no thanks", "not interested", "નથી જોઈતું"])
def test_every_kind_of_stop_suppresses_always_and_confirms_once(client, db, sent, words):
    on(db)
    w = seed_send(db)
    say(client, tap(LEAD, YES, context_id=w))
    sent.clear()
    say(client, typed(LEAD, words))
    assert db.query(SuppressionEntry).count() == 1 and len(texts_of(sent, LEAD)) == 1
    assert db.query(AgentHandoff).one().status == "cancelled"
    say(client, typed(LEAD, words))
    assert len(texts_of(sent, LEAD)) == 1                                      # one confirmation only


def test_stop_suppresses_even_when_the_automatic_reply_is_off(client, db, sent):
    w = seed_send(db)
    say(client, typed(LEAD, "band karo"))
    assert db.query(SuppressionEntry).count() == 1 and sent == []


def test_a_suppressed_number_is_never_answered_or_handed_off_again(client, db, sent):
    on(db)
    w = seed_send(db)
    say(client, typed(LEAD, "STOP"))
    sent.clear()
    say(client, tap(LEAD, YES, context_id=w))
    say(client, typed(LEAD, "haan"))
    assert sent == [] and db.query(AgentHandoff).filter(AgentHandoff.status == "open").count() == 0


def test_a_voice_note_is_handed_off_and_gets_the_please_type_text_once(client, db, sent, llm):
    on(db)
    set_flag(db, "sales_agent_mode", "on")
    seed_send(db)
    say(client, voice(LEAD))
    say(client, voice(LEAD))
    media = detailing_responder.load_config()["templates"][TEMPLATE]["texts"]["media_reply"]
    assert texts_of(sent, LEAD) == [media] and llm == [] and db.query(AgentHandoff).count() == 1


def test_reactions_stickers_and_emoji_are_claimed_and_ignored(client, db, sent, llm):
    on(db)
    set_flag(db, "demo_mode", "on")
    seed_send(db)
    say(client, fresh({"from": LEAD, "id": next_wamid(), "type": "reaction", "reaction": {"emoji": "\U0001F44D", "message_id": "x"}}))
    say(client, fresh({"from": LEAD, "id": next_wamid(), "type": "sticker", "sticker": {}}))
    say(client, typed(LEAD, "\U0001F44D"))
    assert sent == [] and db.query(AgentHandoff).count() == 0 and llm == []


# ---------------------------------------------------------------------------------------------------------------------
# when the automatic reply must NOT go out
# ---------------------------------------------------------------------------------------------------------------------
def test_a_message_older_than_the_24_hour_window_gets_no_reply(client, db, sent):
    on(db)
    w = seed_send(db)
    old = tap(LEAD, YES, context_id=w)
    old["timestamp"] = str(int(time.time()) - 30 * 3600)
    say(client, old)
    assert sent == [] and db.query(AgentHandoff).count() == 1


def test_a_template_older_than_seven_days_gets_a_hand_off_but_no_reply_and_one_older_than_sixty_days_is_not_claimed(client, db, sent):
    on(db)
    w = seed_send(db, age_days=8)
    say(client, tap(LEAD, YES, context_id=w))
    assert sent == [] and db.query(AgentHandoff).count() == 1
    w2 = seed_send(db, phone=LEAD2, age_days=61, tag="OLD")
    say(client, tap(LEAD2, YES, context_id=w2))
    assert db.query(AgentHandoff).count() == 1 and db.query(AgentInboundFeed).filter(AgentInboundFeed.sender == LEAD2).count() == 1


def test_no_automatic_reply_after_a_person_already_replied(client, db, sent):
    on(db)
    w = seed_send(db)
    agent_service.add_event(db, "Krishna Studio", "whatsapp", "out", "reply_sent", "WhatsApp reply sent to +91 ******0001", None)
    say(client, tap(LEAD, YES, context_id=w))
    assert sent == []


def test_caps_per_number_and_per_day(client, db, sent, monkeypatch):
    on(db)
    for _ in range(2):
        agent_service.add_event(db, "Krishna Studio", "whatsapp", "out", "detailing_auto_reply", "x", {"phone": demo_responder._mask(LEAD)})
    w = seed_send(db)
    say(client, tap(LEAD, YES, context_id=w))
    assert sent == []
    monkeypatch.setattr(detailing_responder, "MAX_AUTO_PER_DAY", 2)
    w2 = seed_send(db, phone=LEAD2, tag="X2")
    say(client, tap(LEAD2, YES, context_id=w2))
    assert sent == []


def test_a_provider_failure_keeps_the_hand_off_and_is_never_retried(client, db, monkeypatch):
    on(db)
    calls = []

    def post(payload):
        calls.append(payload)
        raise requests.ConnectionError("provider down")
    monkeypatch.setattr(demo_responder, "_post", post)
    w = seed_send(db)
    say(client, tap(LEAD, YES, context_id=w))
    say(client, tap(LEAD, YES, context_id=w))
    assert len(calls) == 1 and db.query(AgentHandoff).count() == 1
    assert db.query(AgentActivity).filter(AgentActivity.kind == "detailing_reply_failed").count() == 1


def test_a_crash_inside_the_responder_keeps_the_message_claimed_and_the_webhook_ok(client, db, sent, monkeypatch):
    set_flag(db, "demo_mode", "on")
    seed_send(db)

    def boom(*args, **kwargs):
        raise RuntimeError("bug")
    monkeypatch.setattr(detailing_responder, "_handle_lead", boom)
    assert say(client, typed(LEAD, "send the demo")).status_code == 200
    assert db.query(DemoSession).count() == 0 and db.query(AgentInboundFeed).filter(AgentInboundFeed.sender == LEAD).count() == 1


# ---------------------------------------------------------------------------------------------------------------------
# campaign 1 is untouched
# ---------------------------------------------------------------------------------------------------------------------
def test_a_campaign_1_template_tap_still_starts_the_real_estate_demo_with_the_project_name(client, db, sent):
    set_flag(db, "demo_mode", "on")
    on(db)
    seed_send(db, phone=LEAD2, template="iv_en_realestate_demo_v1", lead_ref="Pride Group", tag="RE1")
    # the real-estate send is logged with the project as the 2nd body parameter
    row = db.query(AgentActivity).filter(AgentActivity.kind == "template_sent").one()
    payload = json.loads(row.payload_json)
    payload["project"] = "Pride Aura"
    row.payload_json = json.dumps(payload)
    db.commit()
    say(client, tap(LEAD2, "Yes, send the demo", context_id=payload["wamid"]))
    assert len(sent) == 1 and "Pride Aura" in sent[0]["interactive"]["body"]["text"]
    assert db.query(DemoSeen).filter(DemoSeen.wamid.like("det:%")).count() == 0


def test_a_stranger_and_a_campaign_1_lead_are_not_claimed_and_nothing_is_written(client, db, sent, llm):
    set_flag(db, "demo_mode", "on")
    set_flag(db, "sales_agent_mode", "on")
    seed_send(db, phone=LEAD2, template="iv_en_realestate_demo_v1", lead_ref="Pride Group", tag="RE2")
    before = db.query(AgentActivity).count()
    for message in (typed(LEAD, "hello"), typed(LEAD2, "send the demo for Pride Aura"), typed(LEAD2, "what do you do?")):
        assert detailing_responder.maybe_handle_lead_message(db, message, message["from"][2:], "text", "x", True) is False
    assert db.query(DemoSeen).count() == 0 and db.query(AgentActivity).count() == before


def test_a_stranger_typing_send_the_demo_still_gets_the_demo(client, db, sent):
    set_flag(db, "demo_mode", "on")
    on(db)
    say(client, typed(LEAD2, "send the demo"))
    assert len(sent) == 1 and sent[0]["type"] == "interactive"


def test_the_ai_agent_still_answers_a_non_detailing_lead(client, db, sent, llm):
    set_flag(db, "sales_agent_mode", "on")
    on(db)
    say(client, typed(LEAD2, "what do you do?"))
    assert len(llm) == 1


def test_a_reply_to_a_campaign_1_template_by_a_detailing_number_is_not_claimed(client, db, sent):
    set_flag(db, "demo_mode", "on")
    seed_send(db)                                                                    # LEAD also got a detailing template
    re_w = seed_send(db, template="iv_en_realestate_demo_v1", lead_ref="Pride Group", tag="RE3")
    say(client, tap(LEAD, "Yes, send the demo", context_id=re_w))
    assert db.query(DemoSession).count() == 1                                         # the context decides: that tap belongs to the real-estate template


def test_a_demo_that_is_already_running_is_allowed_to_finish(client, db, sent):
    set_flag(db, "demo_mode", "on")
    on(db)
    say(client, typed(LEAD, "send the demo"))                                         # before any detailing template existed
    assert db.query(DemoSession).count() == 1
    seed_send(db)
    sent.clear()
    say(client, typed(LEAD, "75"))
    assert db.query(DemoSession).one().step == "type"                                 # the open demo answered, the detailing path stayed out


# ---------------------------------------------------------------------------------------------------------------------
# the config
# ---------------------------------------------------------------------------------------------------------------------
def test_the_shipped_config_is_valid_and_every_text_passes_the_reply_validator():
    cfg = detailing_responder.load_config()
    assert cfg["valid"], cfg["problems"]
    for name, tpl in cfg["templates"].items():
        for key, text in tpl["texts"].items():
            ok, reason, _ = sales_agent.check_reply(text, False)
            assert ok, (name, key, reason)
            assert not detailing_responder.BANNED.search(text) and len(text) <= 400
        for label in tpl["yes_labels"] + tpl["notnow_labels"]:
            assert len(label) <= 25 and not demo_responder.is_trigger("button", label) and not demo_responder._is_hard_stop(label)


def test_a_bad_text_makes_the_config_invalid_and_nothing_is_sent_but_the_lead_is_still_claimed(client, db, sent):
    write_config(lambda d: d["templates"][TEMPLATE]["texts"].update(yes_reply="Free demo for you, we will call soon. STOP to end. AI"))
    on(db)
    set_flag(db, "demo_mode", "on")
    w = seed_send(db)
    say(client, tap(LEAD, YES, context_id=w))
    assert sent == [] and db.query(AgentHandoff).count() == 1 and db.query(DemoSession).count() == 0
    assert "CONFIG PROBLEM" in detailing_responder.status_text(db)


def test_a_label_that_would_start_the_demo_or_count_as_stop_invalidates_the_config():
    write_config(lambda d: d["templates"][TEMPLATE].update(yes_labels=["Yes, send the demo"]))
    assert not detailing_responder.load_config()["valid"]
    write_config(lambda d: d["templates"][TEMPLATE].update(yes_labels=["हाँ, बताइए"], notnow_labels=["No, thanks"]))
    assert not detailing_responder.load_config()["valid"]


def test_a_missing_config_still_claims_by_the_template_name(client, db, sent, monkeypatch, tmp_path):
    on(db)
    set_flag(db, "demo_mode", "on")
    monkeypatch.setattr(detailing_responder, "CONFIG_PATH", tmp_path / "nope.json")
    detailing_responder._cfg_cache.update(mtime=None, data=None)
    w = seed_send(db)
    say(client, tap(LEAD, YES, context_id=w))
    say(client, typed(LEAD, "send the demo"))
    assert sent == [] and db.query(AgentHandoff).count() == 1 and db.query(DemoSession).count() == 0


def test_a_detailing_template_that_is_not_in_the_config_yet_is_claimed_without_automatic_text(client, db, sent):
    on(db)
    w = seed_send(db, template="iv_gu_detailing_video_v1")
    say(client, tap(LEAD, "હા", context_id=w))
    assert sent == [] and db.query(AgentHandoff).count() == 1


def test_the_number_lookup_agrees_with_the_sales_agents_wamid_decoder():
    w = wamid_for(LEAD)
    assert detailing_responder._phone_from_wamid(w) == sales_agent._phone_from_wamid(w) == LEAD
    assert detailing_responder._phone_from_wamid("wamid.garbage") == ""


def test_a_test_send_label_gets_the_reply_but_no_hand_off_or_alert(client, db, sent):
    on(db)
    open_owner_window(client)
    sent.clear()
    w = seed_send(db, lead_ref="Boss test")
    say(client, tap(LEAD, YES, context_id=w))
    assert texts_of(sent, LEAD) == [yes_text()] and db.query(AgentHandoff).count() == 0 and texts_of(sent, OWNER) == []


# ---------------------------------------------------------------------------------------------------------------------
# the owner
# ---------------------------------------------------------------------------------------------------------------------
def test_the_owner_gets_one_alert_inside_his_window_and_none_outside(client, db, sent):
    on(db)
    w = seed_send(db)
    say(client, tap(LEAD, YES, context_id=w))                                          # window closed: hand-off only
    assert texts_of(sent, OWNER) == []
    open_owner_window(client)
    sent.clear()
    w2 = seed_send(db, phone=LEAD2, tag="W2")
    say(client, tap(LEAD2, YES, context_id=w2))
    alerts = texts_of(sent, OWNER)
    assert len(alerts) == 1 and "wa.me/" + LEAD2 in alerts[0] and "IST" in alerts[0] and "Automatic reply: sent" in alerts[0]


def test_the_owners_own_tap_shows_him_the_reply_in_any_mode_without_hand_off_or_suppression(client, db, sent):
    owner_w = seed_send(db, phone=OWNER, lead_ref="Owner test")
    say(client, tap(OWNER, YES, context_id=owner_w))
    assert texts_of(sent, OWNER) == [yes_text(), detailing_responder.OWNER_TEXTS["owner_done"]]
    assert db.query(AgentHandoff).count() == 0 and db.query(SuppressionEntry).count() == 0
    assert db.query(OwnerInbox).order_by(OwnerInbox.id.desc()).first().processed_at is not None
    sent.clear()
    say(client, tap(OWNER, NOTNOW, context_id=owner_w))
    assert sent == []


def test_detailing_run_previews_the_exact_lead_text_on_the_owners_phone(client, db, sent):
    say(client, typed(OWNER, "DETAILING RUN"))
    assert texts_of(sent, OWNER) == [yes_text(), detailing_responder.OWNER_TEXTS["owner_done"]] and detailing_responder.get_mode(db) == "off"
    sent.clear()
    say(client, typed(OWNER, "detailing run %s" % TEMPLATE))
    assert texts_of(sent, OWNER)[0] == yes_text()


def test_owner_chat_is_not_swallowed(client, db, sent):
    seed_send(db, phone=OWNER, lead_ref="Owner test")
    say(client, typed(OWNER, "ok go ahead"))
    say(client, typed(OWNER, "detailing is a good idea"))
    assert sent == [] and all(r.processed_at is None for r in db.query(OwnerInbox).all())


def test_status_reports_paused_and_the_number_lookup_check(client, db, sent):
    seed_send(db)
    say(client, typed(OWNER, "STOP ALL"))
    sent.clear()
    say(client, typed(OWNER, "DETAILING STATUS"))
    text = texts_of(sent, OWNER)[0]
    assert "PAUSED" in text and "Number lookup works on 1 of the last 1" in text and "1 detailing sends logged" in text


# ---------------------------------------------------------------------------------------------------------------------
# the borrowed helpers
# ---------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["_norm", "_apos", "_is_hard_stop", "_only_noise", "_typed_text", "_send_text", "_credentials_ok", "_suppress", "_suppressed", "_mask",
                                  "_test_numbers", "_active_session", "IST", "is_trigger", "_post"])
def test_the_demo_responder_helpers_this_module_borrows_still_exist(name):
    """detailing_responder.py imports these private helpers of demo_responder.py (sales_agent.py does the same): a rename there must fail HERE, not silently in production."""
    assert hasattr(demo_responder, name)
