import httpx
from app.config import settings

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE = "https://image.tmdb.org/t/p/w500"
YOUTUBE_BASE = "https://www.youtube.com/watch?v="

_DEFAULT_PARAMS = {"language": "en-US"}
_TIMEOUT = 15.0


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=TMDB_BASE,
        params={"api_key": settings.tmdb_api_key, **_DEFAULT_PARAMS},
        headers={"Accept": "application/json"},
        timeout=_TIMEOUT,
    )


class TMDBService:

    # ── Movies ────────────────────────────────────────────────────────────────

    async def search_movies(self, query: str, filters: dict | None = None) -> list[dict]:
        filters = filters or {}
        params: dict = {"query": query, "include_adult": False, "page": 1}
        if filters.get("year"):
            params["year"] = filters["year"]
        async with _client() as c:
            r = await c.get("/search/movie", params=params)
            r.raise_for_status()
            return [self._slim_movie(m) for m in r.json().get("results", [])[:10]]

    async def get_movie_details(self, movie_id: int) -> dict:
        async with _client() as c:
            r = await c.get(f"/movie/{movie_id}", params={"append_to_response": "credits,videos"})
            r.raise_for_status()
            return self._full_movie(r.json())

    async def get_movie_reviews(self, movie_id: int) -> list[str]:
        async with _client() as c:
            r = await c.get(f"/movie/{movie_id}/reviews")
            r.raise_for_status()
            return [rev["content"][:600] for rev in r.json().get("results", [])[:3]]

    async def get_movie_recommendations(self, movie_id: int) -> list[dict]:
        async with _client() as c:
            r = await c.get(f"/movie/{movie_id}/recommendations", params={"page": 1})
            r.raise_for_status()
            return [self._slim_movie(m) for m in r.json().get("results", [])[:10]]

    async def get_trending_movies(self, pages: int = 1) -> list[dict]:
        results: list[dict] = []
        async with _client() as c:
            for page in range(1, pages + 1):
                r = await c.get("/trending/movie/week", params={"page": page})
                r.raise_for_status()
                results.extend(r.json().get("results", []))
        return [self._slim_movie(m) for m in results]

    def _slim_movie(self, m: dict) -> dict:
        return {
            "id": f"movie_{m['id']}",
            "tmdb_id": m["id"],
            "media_type": "movie",
            "title": m.get("title", ""),
            "year": int(m["release_date"][:4]) if m.get("release_date") else None,
            "overview": m.get("overview", ""),
            "rating": round(m.get("vote_average") or 0, 1) or None,
            "cover_url": f"{TMDB_IMAGE}{m['poster_path']}" if m.get("poster_path") else None,
            "genre_ids": m.get("genre_ids", []),
        }

    def _full_movie(self, m: dict) -> dict:
        crew = m.get("credits", {}).get("crew", [])
        cast = m.get("credits", {}).get("cast", [])
        director = next((p["name"] for p in crew if p.get("job") == "Director"), "")
        trailer = self._pick_trailer(m.get("videos", {}).get("results", []))
        return {
            "id": f"movie_{m['id']}",
            "tmdb_id": m["id"],
            "media_type": "movie",
            "title": m.get("title", ""),
            "year": int(m["release_date"][:4]) if m.get("release_date") else None,
            "overview": m.get("overview", ""),
            "rating": round(m.get("vote_average") or 0, 1) or None,
            "cover_url": f"{TMDB_IMAGE}{m['poster_path']}" if m.get("poster_path") else None,
            "genres": [g["name"] for g in m.get("genres", [])],
            "creator": director,
            "cast_or_characters": [c["name"] for c in cast[:5]],
            "trailer_url": trailer,
            "external_url": f"https://www.themoviedb.org/movie/{m['id']}",
        }

    # ── Series ────────────────────────────────────────────────────────────────

    async def search_series(self, query: str, filters: dict | None = None) -> list[dict]:
        filters = filters or {}
        params: dict = {"query": query, "include_adult": False, "page": 1}
        if filters.get("year"):
            params["first_air_date_year"] = filters["year"]
        async with _client() as c:
            r = await c.get("/search/tv", params=params)
            r.raise_for_status()
            return [self._slim_series(s) for s in r.json().get("results", [])[:10]]

    async def get_series_details(self, series_id: int) -> dict:
        async with _client() as c:
            r = await c.get(f"/tv/{series_id}", params={"append_to_response": "credits,videos"})
            r.raise_for_status()
            return self._full_series(r.json())

    async def get_series_reviews(self, series_id: int) -> list[str]:
        async with _client() as c:
            r = await c.get(f"/tv/{series_id}/reviews")
            r.raise_for_status()
            return [rev["content"][:600] for rev in r.json().get("results", [])[:3]]

    async def get_series_recommendations(self, series_id: int) -> list[dict]:
        async with _client() as c:
            r = await c.get(f"/tv/{series_id}/recommendations", params={"page": 1})
            r.raise_for_status()
            return [self._slim_series(s) for s in r.json().get("results", [])[:10]]

    async def get_trending_series(self, pages: int = 1) -> list[dict]:
        results: list[dict] = []
        async with _client() as c:
            for page in range(1, pages + 1):
                r = await c.get("/trending/tv/week", params={"page": page})
                r.raise_for_status()
                results.extend(r.json().get("results", []))
        return [self._slim_series(s) for s in results]

    def _slim_series(self, s: dict) -> dict:
        return {
            "id": f"series_{s['id']}",
            "tmdb_id": s["id"],
            "media_type": "series",
            "title": s.get("name", ""),
            "year": int(s["first_air_date"][:4]) if s.get("first_air_date") else None,
            "overview": s.get("overview", ""),
            "rating": round(s.get("vote_average") or 0, 1) or None,
            "cover_url": f"{TMDB_IMAGE}{s['poster_path']}" if s.get("poster_path") else None,
            "genre_ids": s.get("genre_ids", []),
        }

    def _full_series(self, s: dict) -> dict:
        cast = s.get("credits", {}).get("cast", [])
        creators = [c["name"] for c in s.get("created_by", [])]
        trailer = self._pick_trailer(s.get("videos", {}).get("results", []))
        return {
            "id": f"series_{s['id']}",
            "tmdb_id": s["id"],
            "media_type": "series",
            "title": s.get("name", ""),
            "year": int(s["first_air_date"][:4]) if s.get("first_air_date") else None,
            "overview": s.get("overview", ""),
            "rating": round(s.get("vote_average") or 0, 1) or None,
            "cover_url": f"{TMDB_IMAGE}{s['poster_path']}" if s.get("poster_path") else None,
            "genres": [g["name"] for g in s.get("genres", [])],
            "creator": ", ".join(creators),
            "cast_or_characters": [c["name"] for c in cast[:5]],
            "seasons": s.get("number_of_seasons"),
            "status": s.get("status"),
            "trailer_url": trailer,
            "external_url": f"https://www.themoviedb.org/tv/{s['id']}",
        }

    # ── Shared ────────────────────────────────────────────────────────────────

    def _pick_trailer(self, videos: list[dict]) -> str | None:
        for v in videos:
            if v.get("site") == "YouTube" and v.get("type") == "Trailer":
                return f"{YOUTUBE_BASE}{v['key']}"
        return None


tmdb = TMDBService()
