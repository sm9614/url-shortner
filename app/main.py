from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, responses
from fastapi.responses import RedirectResponse
from starlette.responses import Response

from app import database, cache, encoder
from app.schemas import ShortenRequest, ShortenResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_db()
    await cache.init_cache()
    yield
    await cache.close_cache()
    await database.close_db()

app = FastAPI(title="URL_Shortner", lifespan=lifespan)

BASEURL = "http://localhost:8000"

@app.post("/shorten", response_model=ShortenResponse)
async def shorten_url(request: ShortenRequest):
    original_url = str(request.url)
    url_id = await database.insert_url(original_url)
    short_code = encoder.encode(url_id)
    await database.update_short_code(url_id, short_code)
    return ShortenResponse(
        short_url=f"{BASEURL}/{short_code}",
        short_code=short_code,
        original_url=original_url,
    )

@app.get("/{short_code}")
async def redirect_to_url(short_code: str):
    cached = await cache.get_cache_url(short_code)
    if cached:
        response = RedirectResponse(url=cached, status_code=307)
        response.headers["X-Cache"] = "HIT"
        return response

    original_url = await database.get_url_by_code(short_code)
    if not original_url:
        raise HTTPException(status_code=404, detail="Short URL not found")

    await cache.set_cache_url(short_code, original_url)
    response = RedirectResponse(url=original_url, status_code=307)
    response.headers["X-Cache"] = "MISS"
    return response