"""Сервер инструментов get_ticket / search_kb. В лекции играет роль MCP-сервера.

Один и тот же код, режим задаёт инфраструктура (env):
  TOOLS_AUTH=static  -> один общий ключ с доступом ко всему (профиль naive)
  TOOLS_AUTH=scoped  -> короткоживущий токен, привязанный к клиенту и тикету (профиль secure)

Каждый вызов пишется в audit log (stdout + AUDIT_LOG), попытка чужого доступа даёт ALERT.

  python tools_server.py serve
  python tools_server.py mint T-1042      # выпустить токен на сессию (secure)
"""
import base64, hashlib, hmac, json, os, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DATA = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
AUTH = os.environ.get("TOOLS_AUTH", "static")
STATIC_KEY = os.environ.get("TOOLS_STATIC_KEY", "dev-admin-key")
SIGNING_KEY = os.environ.get("TOOLS_SIGNING_KEY", "").encode()
TTL = int(os.environ.get("TOOLS_TOKEN_TTL", "300"))
AUDIT_LOG = os.environ.get("AUDIT_LOG", "/tmp/tools-audit.jsonl")

TICKETS = json.load(open(os.path.join(DATA, "tickets.json"), encoding="utf-8"))
KB = json.load(open(os.path.join(DATA, "kb.json"), encoding="utf-8"))


def b64(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def unb64(s): return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def mint(ticket_id):
    t = TICKETS[ticket_id]
    claims = {"sub": t["customer_id"], "tickets": [ticket_id], "exp": int(time.time()) + TTL}
    body = b64(json.dumps(claims).encode())
    return body + "." + hmac.new(SIGNING_KEY, body.encode(), hashlib.sha256).hexdigest()


def principal(token):
    """Возвращает (claims, ошибка). claims=None при отказе."""
    if AUTH == "static":
        return ({"sub": "*", "tickets": "*"}, None) if token == STATIC_KEY else (None, "bad key")
    try:
        body, sig = token.split(".")
        good = hmac.new(SIGNING_KEY, body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, good):
            return None, "bad signature"
        claims = json.loads(unb64(body))
        if claims["exp"] < time.time():
            return None, "token expired"
        return claims, None
    except Exception:
        return None, "malformed token"


def audit(**rec):
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **rec}
    line = json.dumps(rec, ensure_ascii=False)
    print(line, flush=True)
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    if rec.get("decision") == "deny" and rec.get("reason") == "not owner":
        print(f"ALERT cross-tenant access: principal={rec['principal']} tried {rec['args']}", flush=True)


def get_ticket(claims, args):
    tid = args.get("ticket_id", "")
    if tid not in TICKETS:
        return 404, {"error": f"ticket {tid} not found"}, "not found"
    t = TICKETS[tid]
    if claims["sub"] != "*" and tid not in claims["tickets"]:
        return 403, {"error": f"access to {tid} denied for this session"}, "not owner"
    return 200, {"ticket_id": tid, **t}, None


def search_kb(claims, args):
    q = args.get("query", "").lower()
    words = [w for w in q.split() if len(w) > 3]
    hits = [a for a in KB if any(w[:5] in (a["title"] + " " + a["text"]).lower() for w in words)]
    return 200, {"results": hits or KB[:1]}, None


TOOLS = {"get_ticket": get_ticket, "search_kb": search_kb}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def reply(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        self.reply(200, {"ok": True, "auth": AUTH}) if self.path == "/healthz" else self.reply(404, {})

    def do_POST(self):
        name = self.path.rsplit("/", 1)[-1]
        args = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        token = self.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        claims, err = principal(token)
        who = claims["sub"] if claims else "anonymous"
        if not claims:
            audit(tool=name, args=args, principal=who, decision="deny", reason=err)
            return self.reply(401, {"error": err})
        if name not in TOOLS:
            return self.reply(404, {"error": f"unknown tool {name}"})
        code, body, reason = TOOLS[name](claims, args)
        audit(tool=name, args=args, principal=who,
              decision="allow" if code == 200 else "deny", reason=reason)
        self.reply(code, body)


if __name__ == "__main__":
    if sys.argv[1:2] == ["mint"]:
        print(mint(sys.argv[2]))
    else:
        port = int(os.environ.get("PORT", "8080"))
        print(f"tools server on :{port}, auth={AUTH}", flush=True)
        ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()
