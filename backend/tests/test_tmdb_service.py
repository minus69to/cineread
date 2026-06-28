import pytest
from app.services.tmdb_service import tmdb


# ── Movies ────────────────────────────────────────────────────────────────────

async def test_search_movies_returns_results():
    results = await tmdb.search_movies("Inception")
    assert len(results) > 0


async def test_search_movies_shape():
    results = await tmdb.search_movies("Inception")
    first = results[0]
    assert first["media_type"] == "movie"
    assert first["id"].startswith("movie_")
    assert "Inception" in first["title"]
    assert first["cover_url"] is None or first["cover_url"].startswith("https://")


async def test_get_movie_details():
    details = await tmdb.get_movie_details(27205)  # Inception
    assert details["title"] == "Inception"
    assert details["creator"] == "Christopher Nolan"
    assert len(details["genres"]) > 0
    assert details["external_url"] == "https://www.themoviedb.org/movie/27205"


async def test_get_movie_reviews():
    reviews = await tmdb.get_movie_reviews(27205)
    assert isinstance(reviews, list)


async def test_get_trending_movies():
    results = await tmdb.get_trending_movies()
    assert len(results) > 0
    assert results[0]["media_type"] == "movie"


# ── Series ────────────────────────────────────────────────────────────────────

async def test_search_series_returns_results():
    results = await tmdb.search_series("Dark")
    assert len(results) > 0


async def test_search_series_shape():
    results = await tmdb.search_series("Dark")
    first = results[0]
    assert first["media_type"] == "series"
    assert first["id"].startswith("series_")


async def test_get_series_details():
    details = await tmdb.get_series_details(70523)  # Dark (Netflix)
    assert "Dark" in details["title"]
    assert details["seasons"] is not None
    assert details["external_url"] == "https://www.themoviedb.org/tv/70523"


async def test_get_series_reviews():
    reviews = await tmdb.get_series_reviews(70523)
    assert isinstance(reviews, list)


async def test_get_trending_series():
    results = await tmdb.get_trending_series()
    assert len(results) > 0
    assert results[0]["media_type"] == "series"
