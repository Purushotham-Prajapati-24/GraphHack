"""Spike checks against a local Open WebUI v0.12.2: admin login, MCP registration, Pipe install, two chats.

Test-only admin credentials are generated on first run into spike/.env (gitignored) and never printed.
"""

import json
import secrets
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://localhost:3001"
HERE = Path(__file__).parent
ENV = HERE / ".env"
LLM = "gpt-oss:20b-cloud"


def creds():
    if not ENV.exists():
        ENV.write_text(f"OWUI_EMAIL=admin@spike.test\nOWUI_PASSWORD={secrets.token_urlsafe(18)}\n")
    kv = dict(line.split("=", 1) for line in ENV.read_text().splitlines() if "=" in line)
    return kv["OWUI_EMAIL"], kv["OWUI_PASSWORD"]


def call(method, path, body=None, token=None, timeout=180):
    req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body is not None else None)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:500]


def step(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" -> {detail}" if detail else ""))
    return ok


def main():
    email, pw = creds()
    s, r = call("POST", "/api/v1/auths/signin", {"email": email, "password": pw})
    if s != 200:
        s, r = call("POST", "/api/v1/auths/signup", {"name": "Spike Admin", "email": email, "password": pw})
    if not step("admin session", s == 200 and r.get("role") == "admin", f"HTTP {s}"):
        sys.exit(1)
    tok = r["token"]

    mcp = {"url": "http://falkordb-mcp:8080/mcp", "path": "", "type": "mcp", "auth_type": "none", "key": "",
           "config": {"enable": True}, "info": {"id": "falkordb", "name": "FalkorDB"}}
    s, r = call("POST", "/api/v1/configs/tool_servers/verify", mcp, tok)
    step("MCP server verify", s == 200, json.dumps(r)[:160])
    s, r = call("POST", "/api/v1/configs/tool_servers", {"TOOL_SERVER_CONNECTIONS": [mcp]}, tok)
    step("MCP server registered", s == 200, f"HTTP {s}")

    content = (HERE / "pipe_ask_org.py").read_text(encoding="utf-8")
    form = {"id": "ask_org_spike", "name": "Ask the Org (spike)", "content": content,
            "meta": {"description": "Spike pipe over FalkorDB"}}
    s, r = call("GET", "/api/v1/functions/id/ask_org_spike", token=tok)
    s, r = call("POST", "/api/v1/functions/id/ask_org_spike/update" if s == 200 else "/api/v1/functions/create", form, tok)
    step("Pipe function saved", s == 200, f"HTTP {s} {str(r)[:120] if s != 200 else ''}")
    s, r = call("GET", "/api/v1/functions/id/ask_org_spike", token=tok)
    if s == 200 and not r.get("is_active"):
        call("POST", "/api/v1/functions/id/ask_org_spike/toggle", token=tok)

    s, r = call("POST", "/api/chat/completions", {"model": "ask_org_spike", "stream": False,
                "messages": [{"role": "user", "content": "Why does billing-service use Kafka?"}]}, tok)
    ans = r["choices"][0]["message"]["content"] if s == 200 else r
    step("Pipe answered from FalkorDB", s == 200 and "example.org/adr/7" in str(ans), str(ans)[:200])

    s, r = call("POST", "/api/chat/completions", {"model": LLM, "stream": False, "tool_ids": ["server:mcp:falkordb"],
                "messages": [{"role": "user", "content": "Use the FalkorDB tools on graph 'org:spike'. Which system does "
                              "billing-service depend on, and which team owns billing-service? Answer in one sentence."}]},
                tok, timeout=300)
    ans = r["choices"][0]["message"]["content"] if s == 200 else r
    if not step("LLM used FalkorDB MCP tools", s == 200 and "event-bus" in str(ans) and "Payments" in str(ans), str(ans)[:300]):
        print("    raw response:", json.dumps(r)[:1200])


if __name__ == "__main__":
    main()
