from app.validators.ssrf_validator import (
    is_ip_private_or_restricted,
    validate_url_safe_for_retrieval,
)


def test_private_ip_detection():
    # Loopback
    assert is_ip_private_or_restricted("127.0.0.1") is True
    assert is_ip_private_or_restricted("127.0.1.1") is True
    # RFC 1918 Private ranges
    assert is_ip_private_or_restricted("10.0.0.1") is True
    assert is_ip_private_or_restricted("172.16.0.1") is True
    assert is_ip_private_or_restricted("192.168.1.100") is True
    # Link local / Cloud metadata
    assert is_ip_private_or_restricted("169.254.169.254") is True
    # IPv6 loopback
    assert is_ip_private_or_restricted("::1") is True
    # Public IP
    assert is_ip_private_or_restricted("8.8.8.8") is False
    assert is_ip_private_or_restricted("1.1.1.1") is False


def test_url_ssrf_blocking():
    # Invalid schemes
    is_safe, msg = validate_url_safe_for_retrieval("ftp://example.com")
    assert is_safe is False
    assert "scheme" in msg

    is_safe, msg = validate_url_safe_for_retrieval("file:///etc/passwd")
    assert is_safe is False

    # Blocked local hostnames
    is_safe, msg = validate_url_safe_for_retrieval("http://localhost:8000")
    assert is_safe is False

    is_safe, msg = validate_url_safe_for_retrieval("http://127.0.0.1:3000")
    assert is_safe is False

    is_safe, msg = validate_url_safe_for_retrieval("http://169.254.169.254/latest/meta-data")
    assert is_safe is False

    # Valid public URL
    is_safe, msg = validate_url_safe_for_retrieval("https://stripe.com")
    assert is_safe is True
