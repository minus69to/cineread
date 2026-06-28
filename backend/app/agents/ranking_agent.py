from app.agents.state import AgentState


def _media_type_badge(media_type: str) -> str:
    return {"movie": "🎬", "series": "📺", "book": "📚"}.get(media_type, "")


def _score(item: dict, cross_ids: set[str]) -> float:
    score = 0.0
    if item.get("id") in cross_ids:
        score += 10.0
    rating = item.get("rating")
    try:
        score += float(rating) if rating else 7.0
    except (TypeError, ValueError):
        score += 7.0
    return score


def _normalise(raw: dict) -> dict:
    return {
        "id": raw.get("id", ""),
        "media_type": raw.get("media_type", ""),
        "title": raw.get("title", ""),
        "year": raw.get("year"),
        "genres": raw.get("genres", []),
        "rating": raw.get("rating"),
        "overview": raw.get("overview", ""),
        "cover_url": raw.get("cover_url"),
        "creator": raw.get("creator", ""),
        "cast_or_characters": raw.get("cast_or_characters", []),
        "trailer_url": raw.get("trailer_url"),
        "external_url": raw.get("external_url", ""),
        "seasons": raw.get("seasons"),
        "status": raw.get("status"),
        "pages": raw.get("pages"),
        "isbn": raw.get("isbn"),
        "reasoning": raw.get("reasoning", ""),
        "related_media": [],
    }


async def ranking_node(state: AgentState) -> dict:
    cross = state.get("cross_media_connections", [])
    cross_map: dict[str, str] = {c["id"]: c.get("reasoning", "") for c in cross}
    cross_ids = set(cross_map.keys())

    # Pool all candidates
    candidates: list[dict] = []
    for item in state.get("movie_results", []):
        item["media_type"] = item.get("media_type", "movie")
        candidates.append(item)
    for item in state.get("series_results", []):
        item["media_type"] = item.get("media_type", "series")
        candidates.append(item)
    for item in state.get("book_results", []):
        item["media_type"] = item.get("media_type", "book")
        candidates.append(item)

    # Enrich from RAG results (may surface items not in API results)
    existing_ids = {c.get("id") for c in candidates}
    for r in state.get("rag_results", []):
        meta = r.get("metadata", {})
        rag_id = r.get("id", "")
        if rag_id not in existing_ids:
            raw_rating = meta.get("rating", "")
            try:
                parsed_rating = float(raw_rating) if raw_rating else None
            except (TypeError, ValueError):
                parsed_rating = None

            raw_year = meta.get("year", "")
            try:
                parsed_year = int(raw_year) if raw_year else None
            except (TypeError, ValueError):
                parsed_year = None

            candidates.append({
                "id": rag_id,
                "media_type": meta.get("type", ""),
                "title": meta.get("title", ""),
                "year": parsed_year,
                "overview": r.get("document", "")[:300],
                "rating": parsed_rating,
                "genres": [g.strip() for g in meta.get("genres", "").split(",") if g.strip()],
                "creator": meta.get("author", meta.get("director", "")),
                "cover_url": meta.get("cover_url") or None,
                "external_url": meta.get("ol_key", ""),
            })
            existing_ids.add(rag_id)

    # Deduplicate by id AND title (handles TMDB vs RAG ID format mismatch)
    seen_ids: set[str] = set()
    seen_titles: set[str] = set()
    unique: list[dict] = []
    for item in candidates:
        iid = item.get("id", "")
        title_key = item.get("title", "").lower().strip()
        if iid in seen_ids or (title_key and title_key in seen_titles):
            continue
        seen_ids.add(iid)
        if title_key:
            seen_titles.add(title_key)
        if iid in cross_map:
            item["reasoning"] = cross_map[iid]
        unique.append(item)

    # Score and sort
    unique.sort(key=lambda x: _score(x, cross_ids), reverse=True)

    # Prefer diversity: at most 2 per media_type in top 5
    top: list[dict] = []
    type_count: dict[str, int] = {}
    for item in unique:
        mt = item.get("media_type", "")
        if type_count.get(mt, 0) < 2:
            top.append(_normalise(item))
            type_count[mt] = type_count.get(mt, 0) + 1
        if len(top) >= 5:
            break

    # If fewer than 3, relax the diversity cap
    if len(top) < 3:
        top = [_normalise(item) for item in unique[:5]]

    return {"ranked_items": top}
