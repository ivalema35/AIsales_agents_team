# Prototype: automatic reply to the "yes" tap of the detailing template (NOT deployed, NOT in backend/ yet)
Made by the reply-path analyst of workflow w010fsanm on 29 Oct 2026 (design in ../reply_path_analysis.json). Files:
- services/detailing_responder.py (583 lines) + services/detailing_config.json (draft texts, labels must be rebuilt from the final template spec)
- tests/test_detailing_responder.py (636 lines), mutate_detailing.py (27 mutants), crm_detailing_patch.py (anchored patch of api/inbound.py + owner_channel.py)
To adopt: copy into backend/ (services/, tests/), build the config from the final spec, run the whole suite (backend: venv\Scripts\python.exe -m pytest tests -q), run the mutation check, apply the patch twice on a temp copy, 3-lens review, then ONLY on the owner's "deploy it": package + agent/deploy/vps_crm_detailing.sh (to be written, pattern vps_crm_demo.sh). Owner switch = his own WhatsApp: DETAILING TEST / ON / OFF / STATUS. OFF by default.
