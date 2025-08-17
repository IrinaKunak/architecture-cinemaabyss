from secrets import randbelow

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
import httpx, hashlib
from urllib.parse import urljoin
from app.settings import settings

app = FastAPI(title="Cinema Abyss Proxy (Strangler Fig)")

TIMEOUT = httpx.Timeout(10.0, connect=5.0)

def _choose_backend_for_movies() -> tuple[str, str]:
    if not settings.GRADUAL_MIGRATION:
        return settings.MONOLITH_URL, "monolith"

    percent = max(0, min(100, settings.MOVIES_MIGRATION_PERCENT))
    if percent <= 0:
        return settings.MONOLITH_URL, "monolith"
    if percent >= 100:
        return settings.MOVIES_SERVICE_URL, "movies"

    if randbelow(100) < percent:
        return settings.MOVIES_SERVICE_URL, "movies"
    else:
        return settings.MONOLITH_URL, "monolith"

async def _proxy(request: Request, base_url: str, upstream_path: str) -> Response:
    method = request.method.upper()
    target_url = urljoin(base_url.rstrip("/") + "/", upstream_path.lstrip("/"))

    query = str(request.url.query)
    if query:
        target_url = f"{target_url}?{query}"

    body = await request.body()

    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    headers["X-Forwarded-Host"] = request.url.hostname or ""
    headers["X-Forwarded-Proto"] = request.url.scheme
    headers["X-Forwarded-For"] = headers.get("X-Forwarded-For", request.client.host if request.client else "")

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        upstream_resp = await client.request(method, target_url, content=body, headers=headers)

    excluded = {"content-encoding", "transfer-encoding", "connection", "keep-alive"}
    response_headers = [(k, v) for k, v in upstream_resp.headers.items() if k.lower() not in excluded]
    return Response(content=upstream_resp.content, status_code=upstream_resp.status_code, headers=dict(response_headers), media_type=upstream_resp.headers.get("content-type"))

@app.get("/health")
async def health() -> PlainTextResponse:
    return PlainTextResponse("OK")

@app.api_route("/api/movies", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@app.api_route("/api/movies/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def movies_proxy(request: Request, path: str = "") -> Response:
    base_url, name = _choose_backend_for_movies()
    resp = await _proxy(request, base_url, f"/api/movies/{path}".rstrip("/"))
    resp.headers["X-Target-Service"] = name
    return resp

