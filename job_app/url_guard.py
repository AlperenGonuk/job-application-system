"""Ortak URL doğrulama: HTTPS zorunluluğu, izinli host, yönlendirme, özel IP ve boyut/zaman sınırları."""
from __future__ import annotations

import ipaddress
import re
import socket
from http.client import HTTPResponse
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

# --- Yapılandırma ---
ALLOWED_HOSTS: frozenset[str] = frozenset({
    "www.linkedin.com", "linkedin.com",
    "tr.linkedin.com", "uk.linkedin.com",
    "www.kariyer.net", "kariyer.net",
    "www.indeed.com", "indeed.com",
    "tr.indeed.com",
    "www.glassdoor.com", "glassdoor.com",
    "bebee.com", "www.bebee.com",
})
MAX_REDIRECTS = 5
MAX_BODY_BYTES = 2 * 1024 * 1024  # 2 MB
TIMEOUT_SECONDS = 30
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"


class URLValidationError(Exception):
    """URL doğrulama hatası."""


def _is_private_ip(host: str) -> bool:
    """DNS çözümlemesi yaparak hedefin özel/loopback IP olup olmadığını kontrol eder."""
    try:
        for family, _, _, _, sockaddr in socket.getaddrinfo(host, None):
            addr = sockaddr[0]
            ip = ipaddress.ip_address(addr)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return True
    except socket.gaierror:
        return True  # Çözümlenemiyorsa engelle
    return False


def validate_url(url: str) -> str:
    """URL'yi doğrular, temizler ve döndürür. Geçersizse URLValidationError fırlatır."""
    if not url or not isinstance(url, str):
        raise URLValidationError("URL boş veya geçersiz tip")

    url = url.strip()
    parts = urlsplit(url)

    if parts.scheme != "https":
        raise URLValidationError(f"Yalnız HTTPS izinli, şema: {parts.scheme!r}")

    host = (parts.hostname or "").casefold()
    if not host:
        raise URLValidationError("URL'de host bulunamadı")

    if host not in ALLOWED_HOSTS:
        raise URLValidationError(f"Host izinli listede değil: {host!r}")

    if _is_private_ip(host):
        raise URLValidationError(f"Özel/yerel IP adresine istek engellendi: {host!r}")

    return url


class _ValidatedRedirect(HTTPRedirectHandler):
    """Her HTTP yönlendirmesini bağlanmadan önce yeniden doğrular."""
    def __init__(self):
        super().__init__()
        self.redirects = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.redirects += 1
        if self.redirects > MAX_REDIRECTS:
            raise URLValidationError(f"Çok fazla yönlendirme ({MAX_REDIRECTS} aşıldı)")
        validated = validate_url(urljoin(req.full_url, newurl))
        return super().redirect_request(req, fp, code, msg, headers, validated)


def safe_fetch(url: str, *, accept_language: str = "tr-TR,tr;q=0.9,en;q=0.8") -> str:
    """URL'yi doğrular, güvenli şekilde indirir ve metin olarak döndürür."""
    validated = validate_url(url)
    request = Request(validated, headers={
        "User-Agent": USER_AGENT,
        "Accept-Language": accept_language,
    })

    opener = build_opener(_ValidatedRedirect())
    response: HTTPResponse = opener.open(request, timeout=TIMEOUT_SECONDS)

    content_length = response.headers.get("Content-Length")
    if content_length and int(content_length) > MAX_BODY_BYTES:
        raise URLValidationError(f"Yanıt çok büyük: {content_length} bayt (limit {MAX_BODY_BYTES})")

    data = response.read(MAX_BODY_BYTES + 1)
    if len(data) > MAX_BODY_BYTES:
        raise URLValidationError(f"Yanıt gövdesi {MAX_BODY_BYTES} baytı aştı")

    return data.decode("utf-8", "replace")
