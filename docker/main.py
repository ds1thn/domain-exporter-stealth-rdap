#!/usr/bin/env python3
import requests
from datetime import datetime, timezone
from flask import Flask, Response

app = Flask(__name__)

STEALTH_RDAP_BASE = "https://rdap.identitydigital.services/rdap/domain/"

@app.route("/probe")
def probe():
    domain = request_args_target()
    if not domain:
        return Response("target parameter is missing", status=400)

    try:
        resp = requests.get(STEALTH_RDAP_BASE + domain, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        expiry = None
        for event in data.get("events", []):
            if event.get("eventAction") == "expiration":
                expiry = event.get("eventDate")
                break

        if not expiry:
            return Response(f'domain_probe_success{{domain="{domain}"}} 0\n', mimetype="text/plain")

        exp_dt = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
        days_left = (exp_dt - datetime.now(timezone.utc)).days

        body = (
            f'domain_expiry_days{{domain="{domain}"}} {days_left}\n'
            f'domain_probe_success{{domain="{domain}"}} 1\n'
        )
        return Response(body, mimetype="text/plain")

    except Exception:
        return Response(f'domain_probe_success{{domain="{domain}"}} 0\n', mimetype="text/plain")


def request_args_target():
    from flask import request
    return request.args.get("target", "").removeprefix("www.")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9223)
