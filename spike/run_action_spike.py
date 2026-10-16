"""Action spike: can an Open WebUI Action button approve an action as the clicking (non-admin) user?

Needs the spike stack up and `python stub_brain.py` running. Test-only credentials and the service secret are
generated into spike/.env (gitignored) and never printed.
"""

import json
import secrets
import sys

from run_spike import ENV, call, creds, step

ACTION_ID = "approve_spike"
PIPE_MODEL = "ask_org_spike"


def env_value(name, make):
    kv = dict(line.split("=", 1) for line in ENV.read_text().splitlines() if "=" in line)
    if name not in kv:
        kv[name] = make()
        with ENV.open("a") as f:
            f.write(f"{name}={kv[name]}\n")
    return kv[name]


def signin(email, pw):
    s, r = call("POST", "/api/v1/auths/signin", {"email": email, "password": pw})
    return r["token"] if s == 200 else None, r


def new_chat(token, key):
    msgs = [{"id": "m-user-1", "role": "user", "content": "event-bus is degraded. Who do we tell?"},
            {"id": "m-asst-1", "role": "assistant", "content": f"Proposed: open an issue.\n\naction-key: `{key}`"}]
    s, r = call("POST", "/api/v1/chats/new", {"chat": {"title": "action spike", "messages": msgs}}, token)
    return (r["id"], msgs) if s == 200 else (None, r)


def click_approve(token, chat_id, msgs, forged_user=None):
    body = {"model": PIPE_MODEL, "chat_id": chat_id, "id": "m-asst-1", "session_id": "spike", "messages": msgs}
    if forged_user:
        body["user"] = {"id": forged_user}
    return call("POST", f"/api/chat/actions/{ACTION_ID}", body, token)


def main():
    admin_email, admin_pw = creds()
    secret = env_value("SPIKE_SERVICE_SECRET", lambda: secrets.token_urlsafe(24))
    user_email = env_value("OWUI_TEST_EMAIL", lambda: "user@spike.test")
    user_pw = env_value("OWUI_TEST_PASSWORD", lambda: secrets.token_urlsafe(18))

    admin, _ = signin(admin_email, admin_pw)
    if not step("admin session", admin is not None):
        sys.exit(1)

    user, _ = signin(user_email, user_pw)
    if user is None:
        s, r = call("POST", "/api/v1/auths/add", {"name": "Spike User", "email": user_email, "password": user_pw,
                                                   "role": "user"}, admin)
        step("non-admin test user created", s == 200, f"HTTP {s}")
        user, _ = signin(user_email, user_pw)
    s, me = call("GET", "/api/v1/auths/", token=user)
    if not step("non-admin session", user is not None and me.get("role") == "user", f"role={me.get('role')}"):
        sys.exit(1)

    content = open(__file__.replace("run_action_spike.py", "action_approve.py"), encoding="utf-8").read()
    form = {"id": ACTION_ID, "name": "Approve (spike)", "content": content, "meta": {"description": "Approve spike"}}
    s, r = call("GET", f"/api/v1/functions/id/{ACTION_ID}", token=admin)
    s, r = call("POST", f"/api/v1/functions/id/{ACTION_ID}/update" if s == 200 else "/api/v1/functions/create", form, admin)
    step("Action function saved", s == 200, f"HTTP {s} {str(r)[:160] if s != 200 else ''}")
    s, r = call("GET", f"/api/v1/functions/id/{ACTION_ID}", token=admin)
    if not r.get("is_active"):
        call("POST", f"/api/v1/functions/id/{ACTION_ID}/toggle", token=admin)
    if not r.get("is_global"):
        call("POST", f"/api/v1/functions/id/{ACTION_ID}/toggle/global", token=admin)
    s, r = call("GET", f"/api/v1/functions/id/{ACTION_ID}", token=admin)
    step("Action active + global", r.get("is_active") and r.get("is_global"), f"active={r.get('is_active')} global={r.get('is_global')}")
    s, _ = call("POST", f"/api/v1/functions/id/{ACTION_ID}/valves/update", {"SERVICE_SECRET": secret}, admin)
    step("service secret valve set", s == 200, f"HTTP {s}")

    # A Pipe without a saved workspace model entry is invisible to non-admin users ("Model not found").
    model = {"id": PIPE_MODEL, "base_model_id": None, "name": "Ask the Org (spike)", "meta": {}, "params": {},
             "access_grants": [{"principal_type": "user", "principal_id": "*", "permission": "read"}]}
    s, r = call("POST", "/api/v1/models/create", model, admin)
    step("Pipe model entry with public read", s == 200 or "already" in str(r).lower(), f"HTTP {s} {str(r)[:160] if s != 200 else ''}")
    call("GET", "/api/models?refresh=true", token=admin)
    s, models = call("GET", "/api/models", token=user)
    ids = [m["id"] for m in (models or {}).get("data", [])] if s == 200 else []
    step("non-admin sees the Pipe model", PIPE_MODEL in ids, f"visible={ids}")

    chat_id, msgs = new_chat(user, "act:acme:open_issue:event-bus:1")
    step("non-admin chat created", chat_id is not None, str(msgs)[:160] if chat_id is None else "")

    s, r = click_approve(user, chat_id, msgs, forged_user="someone-else")
    step("Approve as non-admin reaches the brain", s == 200 and isinstance(r, dict) and r.get("status") == "approved",
         f"HTTP {s} {json.dumps(r)[:200]}")

    other_chat, _ = new_chat(admin, "act:acme:open_issue:event-bus:2")
    s, r = click_approve(user, other_chat, msgs)
    step("Approve on someone else's chat is refused", s != 200, f"HTTP {s}")

    print(f"    expected owui_user_id in stub_brain.log: {me.get('id')}")


if __name__ == "__main__":
    main()
