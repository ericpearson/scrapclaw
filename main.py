import time
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field
from scrapling.fetchers import StealthyFetcher

app = FastAPI(title="scrapclaw", version="0.1.0")


class SolveRequest(BaseModel):
    cmd: str = Field(default="request.get")
    url: str
    maxTimeout: int = Field(default=60000, ge=1)
    wait: int = Field(default=0, ge=0)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "scrapclaw", "status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1")
async def solve(req: SolveRequest) -> dict[str, Any]:
    start = int(time.time() * 1000)

    try:
        page = await StealthyFetcher.async_fetch(
            req.url,
            headless=True,
            timeout=req.maxTimeout,
            wait=req.wait,
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
