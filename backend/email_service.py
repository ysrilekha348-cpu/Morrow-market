import os
import re
import ipaddress
import logging
import httpx
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse

logger = logging.getLogger("morrow.email")
EMAIL_BASE_URL = "https://integrations.emergentagent.com"
EMAIL_KEY = os.environ["EMERGENT_EMAIL_KEY"]
EMAIL_FROM_NAME = os.environ["EMAIL_FROM_NAME"]
EMAIL_REPLY_TO = os.environ.get("EMAIL_REPLY_TO")

_SHORTENERS = ("bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "goo.gl", "rebrand.ly")
_CRED_ASK = ("reply with your password", "reply with the code", "send your password", "cvv",
             "send us your password", "enter your password below", "confirm your card number",
             "your full card number", "seed phrase", "recovery phrase", "verify your card",
             "social security number", "confirm your bank details")
_HOSTISH = re.compile(r"\b(?:https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})", re.I)


def _host_ok(host: str) -> bool:
    if not host or "xn--" in host:
        return False
    try:
        ipaddress.ip_address(host)
        return False
    except ValueError:
        pass
    return not any(host == s or host.endswith("." + s) for s in _SHORTENERS)


def _same_site(shown: str, real: str) -> bool:
    return shown == real or real.endswith("." + shown) or shown.endswith("." + real)


class _EmailScan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.urls, self.anchors = set(), [], []
        self._href, self._text = None, []

    def handle_starttag(self, tag, attrs):
        self.tags.add(tag.lower())
        self.urls += [v for k, v in attrs if k.lower() in ("href", "src") and v]
        if tag.lower() == "a":
            self._href = dict((k.lower(), v) for k, v in attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.anchors.append((self._href, "".join(self._text)))
            self._href, self._text = None, []


def _assert_safe_email(subject: str, html: str) -> None:
    scan = _EmailScan(); scan.feed(html)
    if scan.tags & {"form", "input", "textarea", "select"}:
        raise ValueError("No forms or input fields in email (G2)")
    body = f"{subject}\n{html}".lower()
    for p in _CRED_ASK:
        if p in body:
            raise ValueError(f"Email asks the recipient for credentials: {p!r} (G2)")
    for url in scan.urls:
        low = url.strip().lower()
        if low.startswith(("mailto:", "tel:", "cid:", "#")):
            continue
        if not low.startswith("https://"):
            raise ValueError(f"Email links/assets must be absolute https: {url!r} (G3)")
        host = urlparse(low).hostname or ""
        if not _host_ok(host) or urlparse(low).username is not None:
            raise ValueError(f"Shortened, numeric-host or credential-bearing URL: {url!r} (G3)")
    for href, text in scan.anchors:
        real = urlparse(href.strip().lower()).hostname or ""
        if not real:
            continue
        for m in _HOSTISH.finditer(text):
            if not _same_site(m.group(1).lower(), real):
                raise ValueError(f"Anchor text {m.group(1)!r} ≠ real link host {real!r} (G3)")


async def send_email(*, to: str, subject: str, html: str) -> str:
    """Raises RuntimeError with a short reason on failure."""
    _assert_safe_email(subject, html)
    payload = {"to": [to], "subject": subject, "html": html, "from_name": EMAIL_FROM_NAME}
    if EMAIL_REPLY_TO:
        payload["contact_email"] = EMAIL_REPLY_TO
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{EMAIL_BASE_URL}/api/v1/email/send", headers={"X-Email-Key": EMAIL_KEY}, json=payload)
        resp.raise_for_status()
        return resp.json().get("id", "")
    except httpx.HTTPStatusError as e:
        try:
            data = e.response.json()
        except ValueError:
            data = {}
        code = data.get("code", "")
        if code in ("insufficient_credits", "integration_disabled", "daily_limit_reached"):
            logger.warning(f"Email paused: {code} ({e.response.status_code}): {data.get('message', '')}")
            raise RuntimeError(data.get("message") or "Email is temporarily unavailable")
        logger.error(f"Email send failed: {e.response.status_code} {e.response.text}")
        raise RuntimeError("Email provider rejected the send")
    except Exception as e:
        logger.error(f"Email send error: {e}")
        raise RuntimeError("Email could not be sent")


def approval_email(order: dict, status_url: str) -> tuple[str, str]:
    brand = escape(EMAIL_FROM_NAME)
    name = escape(order["product_name"])
    url = escape(status_url, quote=True)
    subject = f"Your {EMAIL_FROM_NAME} download is ready: {order['product_name']}"
    html = f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f5f4ef;padding:32px 0">
<tr><td align="center"><table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;background:#ffffff;border:1px solid #d9dbd2">
<tr><td style="background:#29352f;padding:22px 32px;font-family:Georgia,serif;color:#f5f4ef;font-size:18px">{brand}</td></tr>
<tr><td style="padding:36px 32px 8px;font-family:Arial,sans-serif;font-size:11px;letter-spacing:2px;color:#b58e3d">PAYMENT CONFIRMED</td></tr>
<tr><td style="padding:0 32px;font-family:Georgia,serif;font-size:30px;line-height:1.15;color:#29352f">Your download is ready.</td></tr>
<tr><td style="padding:18px 32px 0;font-family:Arial,sans-serif;font-size:14px;line-height:1.7;color:#5f6b63">Thank you for buying <strong style="color:#29352f">{name}</strong>. We've confirmed your GPay payment, and your file is waiting for you.</td></tr>
<tr><td style="padding:28px 32px"><a href="{url}" style="display:inline-block;background:#29352f;color:#f5f4ef;text-decoration:none;font-family:Arial,sans-serif;font-size:13px;font-weight:bold;padding:14px 22px">Open my download</a></td></tr>
<tr><td style="padding:0 32px 30px;font-family:Arial,sans-serif;font-size:12px;line-height:1.6;color:#7a857d">Keep this email. The button always takes you back to your order page, where you can download again any time.</td></tr>
<tr><td style="border-top:1px solid #d9dbd2;padding:18px 32px;font-family:Arial,sans-serif;font-size:11px;color:#9aa29b">Sent by {brand} because you bought from our store. We never ask for your password or card details by email.</td></tr>
</table></td></tr></table>"""
    return subject, html
