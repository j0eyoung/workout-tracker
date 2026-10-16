"""Home Assistant: sensors for today's workout and your streak, and a morning check-in reminder to your phone.

The add-on talks to Home Assistant through the Supervisor (SUPERVISOR_TOKEN, given to add-ons with
homeassistant_api: true), so there is nothing to set up except picking your phone in Settings."""
import json
import os
import urllib.error
import urllib.request

CORE = "http://supervisor/core/api"
SUPERVISOR = "http://supervisor"


def _token():
    return os.getenv("SUPERVISOR_TOKEN", "")


def available():
    return bool(_token())


def _call(method, url, body=None, timeout=10):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {_token()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return json.loads(raw) if raw else None


def set_state(entity_id, state, attributes):
    """Creates or updates a sensor (it lives until Home Assistant restarts; the add-on refreshes it every few minutes)."""
    return _call("POST", f"{CORE}/states/{entity_id}", {"state": str(state)[:255], "attributes": attributes})


def notify_services():
    """Phone notification services from the Home Assistant companion app, e.g. ["mobile_app_joes_pixel"]."""
    try:
        for domain in _call("GET", f"{CORE}/services") or []:
            if domain.get("domain") == "notify":
                names = sorted(domain.get("services", {}).keys())
                return [n for n in names if n.startswith("mobile_app")] + [n for n in names if not n.startswith("mobile_app")]
    except Exception:
        pass
    return []


_panel = {"url": None}


def panel_url():
    """Where a tapped notification opens: this add-on's page in Home Assistant."""
    if _panel["url"] is None:
        try:
            slug = (_call("GET", f"{SUPERVISOR}/addons/self/info") or {}).get("data", {}).get("slug")
            _panel["url"] = f"/hassio/ingress/{slug}" if slug else ""
        except Exception:
            _panel["url"] = ""
    return _panel["url"] or None


def direct_address():
    """This add-on's own address on the home network (host IP plus the published port), for the phone's home screen.
    {"url", "port", "host"}; url is None when the port isn't published in the add-on's Network settings."""
    port, host = None, None
    try:
        net = (_call("GET", f"{SUPERVISOR}/addons/self/info") or {}).get("data", {}).get("network") or {}
        port = net.get("8501/tcp")
    except Exception:
        pass
    try:
        for iface in (_call("GET", f"{SUPERVISOR}/network/info") or {}).get("data", {}).get("interfaces", []):
            addrs = (iface.get("ipv4") or {}).get("address") or []
            if iface.get("primary") and addrs:
                host = addrs[0].split("/")[0]
                break
    except Exception:
        pass
    if not available():   # running outside Home Assistant (local testing)
        port = port or 8501
    return {"url": f"http://{host or 'homeassistant.local'}:{port}/" if port else None, "port": port,
            "host": host, "fallback": f"http://homeassistant.local:{port}/" if port and host else None}


def notify(service, title, message):
    data = {}
    url = panel_url()
    if url:
        data = {"clickAction": url, "url": url}   # Android uses clickAction, iPhone uses url
    return _call("POST", f"{CORE}/services/notify/{service}", {"title": title, "message": message, "data": data})
