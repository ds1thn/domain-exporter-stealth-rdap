#!/usr/bin/env python3
import re
import socket
from datetime import datetime, timezone
from flask import Flask, Response, request

app = Flask(__name__)

STEALTH_RDAP_BASE = "https://rdap.identitydigital.services/rdap/domain/"
TCI_WHOIS_HOST = "whois.tcinet.ru"
TCI_WHOIS_PORT = 43

# только поле "paid-till", без "registered" и прочих ложных срабатываний
PAID_TILL_RE = re.compile(r"^paid-till:\s*(.+)$", re.IGNORECASE | re.MULTILINE)


def whois_query(host, port, query, timeout=10):
    with socket.create_connection((host, port), timeout=timeout) as s:
        s.sendall((query + "\r\n").encode())
        chunks = []
        while True:
            data = s.recv(4096)
            if not data:
                break
            chunks.append(data)
        return b"".join(chunks).decode("utf-8", errors="replace")


def probe_ru_domain(domain):
    body = whois_query(TCI_WHOIS_HOST, TCI_WHOIS_PORT, domain)
    m = PAID_TILL_RE.search(body)
    if not m:
        return None
    date_str = m.group(1).strip()
    # формат TCI: 2026-11-11T13:00:00Z
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))


def probe_stealth_rdap(domain):
    import requests
    resp = requests.get(STEALTH_RDAP_BASE + domain, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    for event in data.get("events", []):
        if event.get("eventAction") == "expiration":
            return datetime.fromisoformat(event["eventDate"].replace("Z", "+00:00"))
    return None


@app.route("/probe")
def probe():
    domain = request.args.get("target", "").removeprefix("www.")
    if not domain:
        return Response("target parameter is missing", status=400)

    try:
        if domain.endswith((".ru", ".xn--p1ai", ".su")):
            expiry = probe_ru_domain(domain)
        else:
            expiry = probe_stealth_rdap(domain)

        if not expiry:
            return Response(f'domain_probe_success{{domain="{domain}"}} 0\n', mimetype="text/plain")

        days_left = (expiry - datetime.now(timezone.utc)).days
        body = (
            f'domain_expiry_days{{domain="{domain}"}} {days_left}\n'
            f'domain_probe_success{{domain="{domain}"}} 1\n'
        )
        return Response(body, mimetype="text/plain")

    except Exception:
        return Response(f'domain_probe_success{{domain="{domain}"}} 0\n', mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9223)