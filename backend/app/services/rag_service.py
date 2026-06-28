import asyncio
from typing import Literal

import chromadb
from sentence_transformers import SentenceTransformer

from app.config import settings

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

_COLLECTION_MAP: dict[str, str] = {
    "movie": "movies",
    "series": "series",
    "book": "books",
}


class RAGService:
    def __init__(self) -> None:
        self._client: chromadb.HttpClient | None = None
        self._model: SentenceTransformer | None = None
        self._collections: dict[str, chromadb.Collection] = {}

    def _init(self) -> None:
        if self._client is not None:
            return
        self._client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
        )
        self._model = SentenceTransformer(EMBEDDING_MODEL)
        for name in _COLLECTION_MAP.values():
            self._collections[name] = self._client.get_or_create_collection(name)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        assert self._model is not None
        return self._model.encode(texts, show_progress_bar=False).tolist()

    def _sync_search_all(self, query: str, n_results: int) -> list[dict]:
        self._init()
        embedding = self._embed([query])
        combined: list[dict] = []
        for collection in self._collections.values():
            try:
                res = collection.query(query_embeddings=embedding, n_results=n_results)
                for i, doc_id in enumerate(res["ids"][0]):
                    combined.append({
                        "id": doc_id,
                        "document": res["documents"][0][i],
                        "metadata": res["metadatas"][0][i],
                        "distance": res["distances"][0][i],
                    })
            except Exception:
                pass
        combined.sort(key=lambda x: x["distance"])
        return combined[: n_results * 2]

    def _sync_search_by_type(self, query: str, media_type: str, n_results: int) -> list[dict]:
        self._init()
        coll_name = _COLLECTION_MAP.get(media_type)
        if not coll_name or coll_name not in self._collections:
            return []
        embedding = self._embed([query])
        res = self._collections[coll_name].query(query_embeddings=embedding, n_results=n_results)
        return [
            {
                "id": res["ids"][0][i],
                "document": res["documents"][0][i],
                "metadata": res["metadatas"][0][i],
                "distance": res["distances"][0][i],
            }
            for i in range(len(res["ids"][0]))
        ]

    async def search_all(self, query: str, n_results: int = 5) -> list[dict]:
        return await asyncio.to_thread(self._sync_search_all, query, n_results)

    async def search_by_type(
        self,
        query: str,
        media_type: Literal["movie", "series", "book"],
        n_results: int = 5,
    ) -> list[dict]:
        return await asyncio.to_thread(self._sync_search_by_type, query, media_type, n_results)


rag = RAGService()
