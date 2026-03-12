import ipaddress
import os
import socket
import time
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from scrapling.fetchers import StealthyFetcher

app = FastAPI(title="scrapclaw", version="0.0.1")

BLOCK_PRIVATE = os.getenv("SCRAPCLAW_BLOCK_PRIVATE_NETWORKS", "true").lower() != "false"
API_TOKEN = os.getenv("SCRAPCLAW_API_TOKEN", "").strip()
ALLOWED_HOSTS = {
    host.strip().lower()
    for host in os.getenv("SCRAPCLAW_ALLOWED_HOSTS", "").split(",")
    if host.strip()
}
MAX_TIMEOUT_MS = int(os.getenv("SCRAPCLAW_MAX_TIMEOUT_MS", "120000"))
MAX_WAIT_MS = int(os.getenv("SCRAPCLAW_MAX_WAIT_MS", "10000"))


class SolveRequest(BaseModel):
    cmd: str = Field(default="request.get")
    url: str
    maxTimeout: int = Field(default=60000, ge=1)
    wait: int = Field(default=0, ge=0)


def _is_blocked_ip(value: str) -> bool:
    ip = ipaddress.ip_address(value)
    return any(
        [
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_multicast,
            ip.is_reserved,
            ip.is_unspecified,
        ]
    )


def _validate_target(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Only http and https URLs are allowed")

    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="URL must include a hostname")

    host = parsed.hostname.lower()
    if host in ALLOWED_HOSTS:
        return

    if not BLOCK_PRIVATE:
        return

    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise HTTPException(status_code=400, detail=f"DNS resolution failed for {host}: {exc}") from exc

    resolved_ips = {info[4][0] for info in infos}
    if any(_is_blocked_ip(ip) for ip in resolved_ips):
        raise HTTPException(
            status_code=403,
            detail=f"Target resolves to a blocked address: {', '.join(sorted(resolved_ips))}",
        )


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "scrapclaw", "status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1")
async def solve(req: SolveRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    start = int(time.time() * 1000)

    if API_TOKEN:
        expected = f"Bearer {API_TOKEN}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")

    if req.cmd != "request.get":
        raise HTTPException(status_code=400, detail="Unsupported cmd")

    _validate_target(req.url)
    timeout_ms = min(req.maxTimeout, MAX_TIMEOUT_MS)
    wait_ms = min(req.wait, MAX_WAIT_MS)

    try:
        page = await StealthyFetcher.async_fetch(
            req.url,
            headless=True,
            timeout=timeout_ms,
            wait=wait_ms,
            solve_cloudflare=True,
        )
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "startTimestamp": start,
            "endTimestamp": int(time.time() * 1000),
            "solution": {},
        }

    return {
        "status": "ok",
        "message": "",
        "startTimestamp": start,
        "endTimestamp": int(time.time() * 1000),
        "solution": {
            "url": str(getattr(page, "url", req.url)),
            "status": getattr(page, "status", 200),
            "response": getattr(page, "html_content", str(page)),
            "cookies": [],
            "userAgent": "",
        },
    }
