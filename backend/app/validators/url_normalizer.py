import re
from urllib.parse import urlparse


def normalize_domain(url_or_domain: str) -> str:
    """
    Normalizes a domain string by:
    - Stripping protocols (http, https)
    - Stripping www.
    - Stripping trailing slashes, paths, query params, ports
    - Converting to lower-case
    Example: 'https://www.STRIPE.com/pricing' -> 'stripe.com'
    """
    if not url_or_domain:
        return ""

    raw = url_or_domain.strip().lower()

    # Prepend scheme if missing for urlparse
    if not (raw.startswith("http://") or raw.startswith("https://")):
        raw = "https://" + raw

    parsed = urlparse(raw)
    hostname = parsed.hostname or ""

    # Strip leading www.
    hostname = hostname.removeprefix("www.")

    # Validate hostname has a valid domain structure
    if not re.match(
        r"^[a-z0-9][a-z0-9-]{0,61}[a-z0-9]?(\.[a-z0-9][a-z0-9-]{0,61}[a-z0-9]?)+$", hostname
    ):
        # Fallback to cleaning raw if weird pattern
        cleaned = (
            re.sub(r"^https?://(www\.)?", "", url_or_domain.strip().lower())
            .split("/")[0]
            .split(":")[0]
        )
        return cleaned

    return hostname


def format_canonical_url(domain: str) -> str:
    """Formats a clean canonical https URL for a normalized domain."""
    clean_domain = normalize_domain(domain)
    return f"https://{clean_domain}" if clean_domain else ""
