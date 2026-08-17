#!/usr/bin/env python3
"""Authenticated CLI for the Audiency support ticket BFF."""
import argparse
import base64
import json
import mimetypes
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, urljoin
from urllib.request import HTTPCookieProcessor, Request, build_opener
from http.cookiejar import CookieJar

SITE = os.getenv("SUPORTE_AUDIENCY_URL", "https://suporte.audiency.io").rstrip("/")
API = os.getenv("SUPORTE_AUDIENCY_API_URL", "https://api.audiency.io").rstrip("/")
ENV_FILE = Path(os.getenv("SUPORTE_AUDIENCY_ENV_FILE", "/mnt/host/.env"))

def read_env(path):
    values = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values

class Client:
    def __init__(self):
        self.jar = CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(self.jar))
        self.user = None

    def request(self, url, method="GET", payload=None, headers=None):
        data = json.dumps(payload).encode() if payload is not None else None
        req = Request(url, data=data, method=method, headers={"Accept": "application/json", **(headers or {})})
        try:
            with self.opener.open(req, timeout=30) as response:
                body = response.read()
                return response.status, body, response.headers, response.url
        except HTTPError as error:
            return error.code, error.read(), error.headers, error.url

    def login(self):
        _, _, _, final_url = self.request(f"{SITE}/home")
        if final_url.rstrip("/").endswith("/home"):
            return
        values = read_env(ENV_FILE)
        email, password = values.get("SUPORTE_AUDIENCY_EMAIL"), values.get("SUPORTE_AUDIENCY_PASSWORD")
        if not email or not password:
            raise RuntimeError("SUPORTE_AUDIENCY_EMAIL/PASSWORD ausentes em /mnt/host/.env")
        code, body, _, _ = self.request(f"{API}/support-rest/auth", "POST", {"email": email, "password": password}, {"Content-Type": "application/json"})
        if code >= 300:
            raise RuntimeError(f"login recusado (HTTP {code})")
        response = json.loads(body)
        data = response.get("data", response)
        token, user = data.get("token"), data.get("user")
        if not token or not user or not user.get("id"):
            raise RuntimeError("login não retornou uma sessão válida")
        # The ticket BFF uses these same browser cookies to identify the user.
        from http.cookiejar import Cookie
        def cookie(name, value):
            return Cookie(0, name, str(value), None, False, "suporte.audiency.io", True, True, "/", True, False, None, True, None, None, {})
        self.jar.set_cookie(cookie("suporte.token", token))
        self.jar.set_cookie(cookie(base64.b64encode(b"userId").decode(), base64.b64encode(str(user["id"]).encode()).decode()))
        self.jar.set_cookie(cookie("suporte.name", user.get("name", "")))
        self.user = user
        code, _, _, final_url = self.request(f"{SITE}/home")
        if code >= 400 or not final_url.rstrip("/").endswith("/home"):
            raise RuntimeError("sessão não foi aceita pela página /home")

    def bff(self, path, method="GET", payload=None):
        code, body, _, _ = self.request(urljoin(f"{SITE}/", path.lstrip("/")), method, payload, {"Content-Type": "application/json"} if payload is not None else {})
        try: result = json.loads(body)
        except json.JSONDecodeError: result = {"raw": body.decode(errors="replace")}
        if code >= 300: raise RuntimeError(result.get("error", result))
        return result.get("data", result)

def require(client): client.login(); return client
def tickets(client, args):
    query = {k: v for k, v in {"status": args.status, "title": args.title, "operatorId": args.operator_id, "orderBy": args.order_by}.items() if v}
    data = client.bff("/api/chamados/tickets" + ("?" + urlencode(query) if query else ""))
    if args.assignee:
        needle = args.assignee.casefold(); data = [t for t in data if any(needle in a.get("name", "").casefold() for a in t.get("assignees", []))]
    print(json.dumps(data, ensure_ascii=False, indent=2))
def show(client, args): print(json.dumps(client.bff(f"/api/chamados/tickets/{args.ticket_id}"), ensure_ascii=False, indent=2))
def comments(client, args): print(json.dumps(client.bff(f"/api/chamados/tickets/{args.ticket_id}/messages"), ensure_ascii=False, indent=2))
def create(client, args):
    payload = {"title": args.title, "module": args.module, "type": args.type, "priority": "media", "description": args.description, "reproductionOrImpact": args.reproduction, "pageUrl": args.page_url, "createdById": client.user["id"], "createdByName": client.user.get("name", "")}
    print(json.dumps(client.bff("/api/chamados/tickets", "POST", payload), ensure_ascii=False, indent=2))
def assign(client, args):
    ticket = client.bff(f"/api/chamados/tickets/{args.ticket_id}")
    ids = list(dict.fromkeys([*ticket.get("assigneeIds", []), args.developer_id]))
    print(json.dumps(client.bff(f"/api/chamados/tickets/{args.ticket_id}", "PATCH", {"assigneeIds": ids}), ensure_ascii=False, indent=2))
def comment(client, args): print(json.dumps(client.bff(f"/api/chamados/tickets/{args.ticket_id}/messages", "POST", {"userName": client.user.get("name", ""), "content": args.text}), ensure_ascii=False, indent=2))
def advance(client, args):
    ticket = client.bff(f"/api/chamados/tickets/{args.ticket_id}")
    flow = {"a_fazer":"em_desenvolvimento", "pendente_resposta":"em_desenvolvimento", "em_desenvolvimento":"revisao", "pausado":"em_desenvolvimento", "revisao":"concluido"}
    target = flow.get(ticket.get("status"))
    if not target: raise RuntimeError(f"sem próximo status para {ticket.get('status')}")
    payload = {"status": target}
    if target == "pausado": payload["pauseReason"] = args.reason
    print(json.dumps(client.bff(f"/api/chamados/tickets/{args.ticket_id}", "PATCH", payload), ensure_ascii=False, indent=2))
def download(client, args):
    ticket = client.bff(f"/api/chamados/tickets/{args.ticket_id}")
    messages = client.bff(f"/api/chamados/tickets/{args.ticket_id}/messages")
    files = list(ticket.get("attachments", [])) + [f for m in messages for f in m.get("attachments", [])]
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    for item in files:
        status, body, _, _ = client.request(urljoin(f"{SITE}/", item["url"].lstrip("/")))
        if status >= 300: raise RuntimeError(f"falha ao baixar anexo {item.get('id')}")
        (out / item["name"]).write_bytes(body)
        print(out / item["name"])

def main():
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="command", required=True)
    def ticket_cmd(name, fn): q=sub.add_parser(name); q.add_argument("ticket_id", type=int); q.set_defaults(fn=fn); return q
    q=sub.add_parser("list"); q.add_argument("--status"); q.add_argument("--assignee"); q.add_argument("--title"); q.add_argument("--operator-id"); q.add_argument("--order-by", default="id-desc"); q.set_defaults(fn=tickets)
    ticket_cmd("show", show); ticket_cmd("comments", comments)
    q=sub.add_parser("create"); q.add_argument("--title",required=True); q.add_argument("--module",required=True); q.add_argument("--type",choices=["bug","melhoria","nova_funcionalidade"],required=True); q.add_argument("--description",required=True); q.add_argument("--reproduction",required=True); q.add_argument("--page-url",required=True); q.set_defaults(fn=create)
    q=ticket_cmd("assign", assign); q.add_argument("--developer-id",type=int,required=True)
    q=ticket_cmd("comment", comment); q.add_argument("--text",required=True)
    q=ticket_cmd("advance", advance); q.add_argument("--reason")
    q=ticket_cmd("download", download); q.add_argument("--output",required=True)
    args=p.parse_args(); client=require(Client()); args.fn(client,args)
if __name__ == "__main__":
    try: main()
    except Exception as error: print(f"erro: {error}", file=sys.stderr); sys.exit(1)
