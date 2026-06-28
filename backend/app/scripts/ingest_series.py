"""
Ingest top-rated TV series from TMDB into ChromaDB with LLM-generated enrichment.
Run from backend/: python -m app.scripts.ingest_series
"""
import asyncio
import json
import re
import urllib.parse

import chromadb
import httpx
from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer

from app.config import settings

TMDB_BASE = "https://api.themoviedb.org/3"
WIKI_BASE = "https://en.wikipedia.org/api/rest_v1/page/summary"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
PAGES = 15        # 15 × 20 = 300 series
BATCH_SIZE = 50
TMDB_DELAY = 0.15
LLM_DELAY = 0.3


def _tmdb_params() -> dict:
    return {"api_key": settings.tmdb_api_key, "language": "en-US"}


def _llm_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={"HTTP-Referer": "https://cineread.app", "X-Title": "CineRead"},
    )


async def _wiki_summary(client: httpx.AsyncClient, title: str) -> str:
    try:
        slug = urllib.parse.quote(title.replace(" ", "_"))
        r = await client.get(f"{WIKI_BASE}/{slug}", follow_redirects=True)
        if r.status_code == 200:
            return r.json().get("extract", "")[:400]
    except Exception:
        pass
    return ""


async def _llm_enrich(llm: AsyncOpenAI, title: str, year, genres: str, creator: str, overview: str) -> dict:
    prompt = f"""TV Series: {title} ({year})
Genres: {genres}
Creator: {creator}
Overview: {overview[:400]}

Return ONLY valid JSON (no markdown):
{{
  "themes": ["5-8 specific narrative themes e.g. time travel, political intrigue, survival, identity"],
  "mood": ["3-5 mood descriptors e.g. dark, tense, atmospheric, slow burn"],
  "style": ["2-4 style terms e.g. anthology, non-linear, prestige drama, mystery box"],
  "keywords": ["5-8 search keywords e.g. unreliable narrator, ensemble cast, cliffhanger"],
  "similar_to": ["3-5 TV series titles with genuinely similar feel or theme"]
}}"""

    try:
        resp = await llm.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=350,
        )
        text = resp.choices[0].message.content or ""
        text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"    LLM enrichment failed for '{title}': {e}")
        return {}


def _build_doc(details: dict, wiki: str, enrichment: dict) -> str:
    parts = [
        f"Title: {details['title']} ({details.get('year', '')})",
        f"Creator: {details.get('creator', '')}",
        f"Genres: {', '.join(details.get('genres', []))}",
        f"Cast: {', '.join(details.get('cast', []))}",
        f"Seasons: {details.get('seasons', '')} | Status: {details.get('status', '')}",
    ]

    if enrichment.get("themes"):
        parts.append(f"Themes: {', '.join(enrichment['themes'])}")
    if enrichment.get("mood"):
        parts.append(f"Mood: {', '.join(enrichment['mood'])}")
    if enrichment.get("style"):
        parts.append(f"Style: {', '.join(enrichment['style'])}")
    if enrichment.get("keywords"):
        parts.append(f"Keywords: {', '.join(enrichment['keywords'])}")
    if enrichment.get("similar_to"):
        parts.append(f"Similar to: {', '.join(enrichment['similar_to'])}")

    parts.append(f"Overview: {details.get('overview', '')}")
    if wiki:
        parts.append(f"Plot context: {wiki}")

    return "\n".join(p for p in parts if p.strip() and not p.endswith(": "))


async def main() -> None:
    print("=== CineRead Series Ingest (with LLM enrichment) ===")
    print("Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print("Connecting to ChromaDB...")
    chroma = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    collection = chroma.get_or_create_collection("series")
    print(f"Collection currently has {collection.count()} series. Will upsert all with enriched docs.")

    print(f"Fetching top-rated series list ({PAGES} pages from TMDB)...")
    stubs: list[dict] = []
    async with httpx.AsyncClient(base_url=TMDB_BASE, params=_tmdb_params(), timeout=15.0) as tc:
        for page in range(1, PAGES + 1):
            r = await tc.get("/tv/top_rated", params={"page": page})
            r.raise_for_status()
            stubs.extend(r.json().get("results", []))
            await asyncio.sleep(0.05)
    print(f"Found {len(stubs)} series. Starting enriched ingest...\n")

    docs, metas, ids = [], [], []
    ingested = errors = 0
    processed_ids: set[str] = set()
    llm = _llm_client()

    async with httpx.AsyncClient(base_url=TMDB_BASE, params=_tmdb_params(), timeout=15.0) as tc, \
               httpx.AsyncClient(timeout=10.0) as wiki_client:

        for i, stub in enumerate(stubs, 1):
            sid = stub["id"]
            item_id = f"series_{sid}"

            if item_id in processed_ids:
                continue
            processed_ids.add(item_id)

            try:
                r = await tc.get(f"/tv/{sid}", params={"append_to_response": "credits"})
                r.raise_for_status()
                raw = r.json()

                cast_list = raw.get("credits", {}).get("cast", [])
                creators = [c["name"] for c in raw.get("created_by", [])]

                details = {
                    "title": raw.get("name", ""),
                    "year": int(raw["first_air_date"][:4]) if raw.get("first_air_date") else None,
                    "creator": ", ".join(creators),
                    "genres": [g["name"] for g in raw.get("genres", [])],
                    "cast": [c["name"] for c in cast_list[:5]],
                    "seasons": raw.get("number_of_seasons"),
                    "status": raw.get("status", ""),
                    "overview": raw.get("overview", ""),
                    "rating": raw.get("vote_average"),
                }

                wiki = await _wiki_summary(wiki_client, details["title"])

                enrichment = await _llm_enrich(
                    llm,
                    details["title"],
                    details.get("year", ""),
                    ", ".join(details["genres"]),
                    details["creator"],
                    details["overview"],
                )

                doc = _build_doc(details, wiki, enrichment)

                docs.append(doc)
                metas.append({
                    "tmdb_id": str(sid),
                    "type": "series",
                    "title": details["title"],
                    "year": str(details.get("year") or ""),
                    "genres": ", ".join(details["genres"]),
                    "seasons": str(details.get("seasons") or ""),
                    "status": details.get("status", ""),
                    "rating": str(round(details.get("rating") or 0, 1)),
                })
                ids.append(item_id)
                ingested += 1

                if i % 10 == 0:
                    print(f"  [{i}/{len(stubs)}] {details['title']} — themes: {enrichment.get('themes', [])[:3]}")

                if len(docs) >= BATCH_SIZE:
                    embs = model.encode(docs).tolist()
                    collection.upsert(documents=docs, embeddings=embs, metadatas=metas, ids=ids)
                    print(f"  Flushed batch. Ingested so far: {ingested}")
                    docs, metas, ids = [], [], []

                await asyncio.sleep(TMDB_DELAY + LLM_DELAY)

            except Exception as e:
                print(f"  ERROR series {sid}: {e}")
                errors += 1

    if docs:
        embs = model.encode(docs).tolist()
        collection.upsert(documents=docs, embeddings=embs, metadatas=metas, ids=ids)

    print(f"\nDone! Ingested={ingested}, Errors={errors}")
    print(f"Total series in collection: {collection.count()}")


if __name__ == "__main__":
    asyncio.run(main())
