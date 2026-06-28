import pytest
from app.services.book_service import books


async def test_search_books_returns_results():
    results = await books.search_books("Dune Frank Herbert")
    assert len(results) > 0


async def test_search_books_shape():
    results = await books.search_books("Dune Frank Herbert")
    first = results[0]
    assert first["media_type"] == "book"
    assert first["id"].startswith("book_")
    assert first["title"] != ""


async def test_search_books_gone_girl():
    results = await books.search_books("Gone Girl Gillian Flynn")
    assert len(results) > 0
    titles = [r["title"] for r in results]
    assert any("Gone Girl" in t for t in titles)


async def test_search_books_has_author():
    results = await books.search_books("1984 George Orwell")
    assert len(results) > 0
    first = results[0]
    assert first["creator"] != ""


async def test_get_book_cover_url():
    url = books.get_book_cover("9780441013593")  # Dune
    assert "covers.openlibrary.org" in url
    assert "9780441013593" in url


async def test_get_book_details_returns_dict():
    result = await books.get_book_details("9780062316110")  # Gone Girl
    assert result["media_type"] == "book"
    assert result["isbn"] == "9780062316110"
    assert result["id"] == "book_9780062316110"
