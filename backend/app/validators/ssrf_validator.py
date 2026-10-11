import ipaddress
import socket
from urllib.parse import urlparse

BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "169.254.169.254",
    "instance-data",
}


def is_ip_private_or_restricted(ip_str: str) -> bool:
    """Checks whether an IP address is private, loopback, link-local, multicast, or reserved."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return True


def validate_url_safe_for_retrieval(url: str) -> tuple[bool, str]:
    """
    Validates that a URL is safe to retrieve:
    - Scheme must be http or https
    - Host cannot be empty or a restricted hostname
    - DNS resolution cannot resolve to a private/loopback/metadata IP
    Returns (is_safe, reason_or_error_message).
    """
    if not url or not isinstance(url, str):
        return False, "URL is empty or invalid"

    try:
        parsed = urlparse(url.strip())
    except Exception as e:
        return False, f"Failed to parse URL: {e!s}"

    if parsed.scheme.lower() not in ("http", "https"):
        return (
            False,
            f"Unsupported URL scheme '{parsed.scheme}'. Only http and https are permitted.",
        )

    hostname = parsed.hostname
    if not hostname:
        return False, "URL missing valid hostname."

    hostname_lower = hostname.lower()

    if hostname_lower in BLOCKED_HOSTNAMES:
        return False, f"Target host '{hostname}' is a restricted local or cloud metadata host."

    # Direct IP literal check
    try:
        ip = ipaddress.ip_address(hostname_lower)
        if is_ip_private_or_restricted(str(ip)):
            return (
                False,
                f"Target IP '{hostname}' belongs to a private or restricted network range.",
            )
    except ValueError:
        # Hostname is a domain name, resolve its IPs
        try:
            # Resolve DNS safely
            addr_info = socket.getaddrinfo(
                hostname_lower, None, socket.AF_UNSPEC, socket.SOCK_STREAM
            )
            for item in addr_info:
                sockaddr = item[4]
                resolved_ip = sockaddr[0]
                if is_ip_private_or_restricted(resolved_ip):
                    return (
                        False,
                        f"Resolved IP '{resolved_ip}' for host '{hostname}' is in a private or restricted address space.",
                    )
        except socket.gaierror:
            return False, f"DNS resolution failed for host '{hostname}'."
        except Exception as e:
            return False, f"DNS validation error for host '{hostname}': {e!s}"

    return True, "URL is valid and safe for retrieval."
