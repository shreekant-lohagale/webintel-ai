
import hashlib
import re
import unicodedata
from urllib.parse import (
    parse_qsl,
    urlencode,
    urlsplit,
    urlunsplit,
)

from bs4 import BeautifulSoup


TRACKING_PARAMETERS = {
    "fbclid",
    "gclid",
    "msclkid",
    "ref_src",
}


def clean_text(value: str | None) -> str:
    """Normalize text without changing its meaning."""

    if not value:
        return ""

    text = unicodedata.normalize("NFKC", value)

    text = text.replace("\u00a0", " ")
    text = text.replace("\u200b", "")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_html(html: str | None) -> str:
    """Extract meaningful text from an HTML fragment."""

    if not html:
        return ""

    soup = BeautifulSoup(html, "lxml")

    for tag in soup.select(
        "script, style, noscript, template"
    ):
        tag.decompose()

    return clean_text(
        soup.get_text(separator=" ", strip=True)
    )


def normalize_tags(tags: list[str] | None) -> list[str]:
    """Normalize and deduplicate tags."""

    seen = set()
    normalized = []

    for tag in tags or []:
        if not isinstance(tag, str):
            continue

        value = clean_text(tag).lower()

        if value and value not in seen:
            seen.add(value)
            normalized.append(value)

    return normalized


def canonicalize_url(url: str) -> str:
    """Normalize common URL variations."""

    parts = urlsplit(url.strip())

    scheme = parts.scheme.lower()

    if scheme not in ("http", "https"):
        raise ValueError("Only HTTP/HTTPS URLs are supported")

    if not parts.hostname:
        raise ValueError("URL must contain a hostname")

    if parts.username or parts.password:
        raise ValueError("Credential-bearing URLs are not supported")

    hostname = parts.hostname.lower()

    if ":" in hostname:
        hostname = f"[{hostname}]"

    port = parts.port

    if (scheme == "http" and port == 80) or (
        scheme == "https" and port == 443
    ):
        port = None

    netloc = hostname + (f":{port}" if port else "")

    parameters = parse_qsl(
        parts.query,
        keep_blank_values=True,
    )

    parameters = [
        (key, value)
        for key, value in parameters
        if not key.lower().startswith("utm_")
        and key.lower() not in TRACKING_PARAMETERS
    ]

    parameters.sort()

    path = parts.path or "/"

    return urlunsplit((
        scheme,
        netloc,
        path,
        urlencode(parameters),
        "",
    ))


def sha256_hash(text: str) -> str:
    """Return a deterministic SHA-256 hex digest."""

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()
