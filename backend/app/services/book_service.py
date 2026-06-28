import httpx

OL_BASE = "https://openlibrary.org"
OL_COVERS_ID = "https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
OL_COVERS_ISBN = "https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
GOOGLE_BOOKS_BASE = "https://www.googleapis.com/books/v1"
_TIMEOUT = httpx.Timeout(connect=5.0, read=12.0, write=5.0, pool=5.0)


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        headers={"Accept": "application/json"},
        timeout=_TIMEOUT,
        follow_redirects=True,
    )


class BookService:

    async def search_books(self, query: str) -> list[dict]:
        async with _client() as c:
            r = await c.get(
                f"{OL_BASE}/search.json",
                params={
                    "q": query,
                    "fields": "key,title,author_name,subject,isbn,first_publish_year,cover_i,ratings_average,number_of_pages_median",
                    "limit": 10,
                    "language": "eng",
                },
            )
            r.raise_for_status()
            docs = r.json().get("docs", [])
            return [self._normalize_doc(doc) for doc in docs if doc.get("title")]

    async def get_book_details(self, isbn: str) -> dict:
        ol_data: dict = {}
        async with _client() as c:
            try:
                r = await c.get(f"{OL_BASE}/isbn/{isbn}.json")
                if r.status_code == 200:
                    ol_data = r.json()
            except httpx.HTTPError:
                pass

            description = self._extract_description(ol_data)
            if not description:
                description = await self._google_books_description(c, isbn)

        return {
            "id": f"book_{isbn}",
            "isbn": isbn,
            "media_type": "book",
            "title": ol_data.get("title", ""),
            "overview": description,
            "cover_url": self.get_book_cover(isbn),
            "pages": ol_data.get("number_of_pages"),
            "external_url": f"https://openlibrary.org/isbn/{isbn}",
        }

    def get_book_cover(self, isbn: str) -> str:
        return OL_COVERS_ISBN.format(isbn=isbn)

    def _normalize_doc(self, doc: dict) -> dict:
        isbn_list = doc.get("isbn", [])
        isbn = isbn_list[0] if isbn_list else ""

        cover_url: str | None = None
        if doc.get("cover_i"):
            cover_url = OL_COVERS_ID.format(cover_id=doc["cover_i"])
        elif isbn:
            cover_url = self.get_book_cover(isbn)

        ol_key = doc.get("key", "")
        item_id = f"book_{isbn}" if isbn else f"book_{ol_key.replace('/', '_').strip('_')}"

        return {
            "id": item_id,
            "isbn": isbn,
            "media_type": "book",
            "title": doc.get("title", ""),
            "creator": ", ".join(doc.get("author_name", [])[:2]),
            "year": doc.get("first_publish_year"),
            "genres": doc.get("subject", [])[:6],
            "rating": round(doc["ratings_average"], 1) if doc.get("ratings_average") else None,
            "pages": doc.get("number_of_pages_median"),
            "cover_url": cover_url,
            "overview": "",
            "external_url": f"https://openlibrary.org{ol_key}",
        }

    def _extract_description(self, ol_data: dict) -> str:
        desc = ol_data.get("description", "")
        if isinstance(desc, dict):
            return desc.get("value", "")
        return desc or ""

    async def _google_books_description(self, client: httpx.AsyncClient, isbn: str) -> str:
        try:
            r = await client.get(
                f"{GOOGLE_BOOKS_BASE}/volumes",
                params={"q": f"isbn:{isbn}"},
            )
            if r.status_code == 200:
                items = r.json().get("items", [])
                if items:
                    return items[0].get("volumeInfo", {}).get("description", "")
        except httpx.HTTPError:
            pass
        return ""


books = BookService()
