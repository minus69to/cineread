from pydantic import BaseModel
from typing import Optional


class MediaItem(BaseModel):
    id: str                         # "movie_157336" / "series_1418" / "book_9780441013593"
    media_type: str                 # "movie" / "series" / "book"
    title: str
    year: Optional[int] = None
    genres: list[str] = []
    rating: Optional[float] = None
    overview: str = ""
    cover_url: Optional[str] = None
    creator: str = ""               # Director / Showrunner / Author
    cast_or_characters: list[str] = []
    trailer_url: Optional[str] = None
    external_url: str = ""

    # Series-specific
    seasons: Optional[int] = None
    status: Optional[str] = None    # "Ended" / "Returning Series"

    # Book-specific
    pages: Optional[int] = None
    isbn: Optional[str] = None

    # Agent-populated
    reasoning: str = ""
    related_media: list[str] = []
