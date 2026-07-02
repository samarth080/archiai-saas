import socket

import pytest

from app.utils.ssrf import UnsafeURLError, assert_public_url


def _resolver_returning(*ips: str):
    """Build a getaddrinfo-style resolver that always returns the given IPs."""
    def resolve(host, port):
        results = []
        for ip in ips:
            if ":" in ip:
                results.append((socket.AF_INET6, socket.SOCK_STREAM, 6, "", (ip, 0, 0, 0)))
            else:
                results.append((socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 0)))
        return results
    return resolve


def _raising_resolver(host, port):
    raise socket.gaierror("name resolution failed")


def test_public_url_passes():
    url = "https://example.com/public-guide"
    assert assert_public_url(url, resolver=_resolver_returning("93.184.216.34")) == url


@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata (link-local)
        "http://127.0.0.1/",                          # loopback
        "http://10.0.0.1/",                           # private
        "http://192.168.1.1/",                        # private
        "http://172.16.0.5/",                         # private
        "http://[::1]/",                              # IPv6 loopback
        "http://0.0.0.0/",                            # unspecified
    ],
)
def test_rejects_non_public_ip_literals(url):
    # IP literals resolve without DNS, so these are hermetic.
    with pytest.raises(UnsafeURLError):
        assert_public_url(url)


def test_rejects_localhost():
    with pytest.raises(UnsafeURLError):
        assert_public_url("http://localhost/")


def test_rejects_ipv4_mapped_ipv6_loopback():
    with pytest.raises(UnsafeURLError):
        assert_public_url("http://[::ffff:127.0.0.1]/")


@pytest.mark.parametrize("scheme_url", ["ftp://example.com/x", "file:///etc/passwd", "gopher://x"])
def test_rejects_non_http_schemes(scheme_url):
    with pytest.raises(UnsafeURLError):
        assert_public_url(scheme_url)


def test_rejects_dns_rebinding_to_private_ip():
    # Public-looking hostname that (per the resolver) maps to a private address.
    with pytest.raises(UnsafeURLError):
        assert_public_url(
            "https://sneaky.example.com/", resolver=_resolver_returning("10.1.2.3")
        )


def test_rejects_any_private_when_multiple_addresses():
    # If a host returns one public and one private address, reject (fail closed).
    with pytest.raises(UnsafeURLError):
        assert_public_url(
            "https://mixed.example.com/",
            resolver=_resolver_returning("93.184.216.34", "127.0.0.1"),
        )


def test_resolution_failure_fails_closed():
    with pytest.raises(UnsafeURLError):
        assert_public_url("https://does-not-resolve.invalid/", resolver=_raising_resolver)


def test_rejects_missing_host():
    with pytest.raises(UnsafeURLError):
        assert_public_url("http:///nohost")
