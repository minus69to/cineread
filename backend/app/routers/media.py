from fastapi import APIRouter, HTTPException, Query

from app.services.book_service import books
from app.services.tmdb_service import tmdb

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    type: str = Query("all", pattern="^(all|movie|series|book)$"),
    page: int = Query(1, ge=1),
):
    results = []

    if type in ("all", "movie"):
        movies = await tmdb.search_movies(q)
        results.extend(movies)

    if type in ("all", "series"):
        series = await tmdb.search_series(q)
        results.extend(series)

    if type in ("all", "book"):
        bks = await books.search_books(q)
        results.extend(bks)

    return {"results": results, "query": q, "type": type}


@router.get("/{media_id}")
async def get_media(media_id: str):
    parts = media_id.split("_", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid media_id format. Use movie_123, series_456, or book_isbn")

    kind, raw_id = parts

    if kind == "movie":
        try:
            return await tmdb.get_movie_details(int(raw_id))
        except Exception:
            raise HTTPException(status_code=404, detail="Movie not found")

    if kind == "series":
        try:
            return await tmdb.get_series_details(int(raw_id))
        except Exception:
            raise HTTPException(status_code=404, detail="Series not found")

    if kind == "book":
        try:
            return await books.get_book_details(raw_id)
        except Exception:
            raise HTTPException(status_code=404, detail="Book not found")

    raise HTTPException(status_code=400, detail=f"Unknown media type: {kind}")
