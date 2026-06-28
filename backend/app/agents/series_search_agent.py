from app.agents.state import AgentState
from app.services.tmdb_service import tmdb

_SKIP = {"movie_only", "book_only"}


async def series_search_node(state: AgentState) -> dict:
    if state.get("search_strategy") in _SKIP:
        return {"series_results": []}

    ref_titles = state.get("reference_titles", [])
    ref_lower = {t.lower() for t in ref_titles}

    if ref_titles:
        # Find the reference title's TMDB ID, then fetch TMDB recommendations
        search_hits = await tmdb.search_series(ref_titles[0])
        if search_hits:
            ref_id = search_hits[0].get("tmdb_id")
            results = await tmdb.get_series_recommendations(ref_id)
        else:
            results = []
    else:
        # No reference title — TMDB search doesn't handle descriptive phrases well,
        # so return nothing; RAG handles semantic search
        results = []

    # Exclude the referenced title itself
    results = [r for r in results if r.get("title", "").lower() not in ref_lower]

    return {"series_results": results}
