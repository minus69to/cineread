from app.agents.state import AgentState
from app.services.tmdb_service import tmdb

_SKIP = {"series_only", "book_only"}


async def movie_search_node(state: AgentState) -> dict:
    if state.get("search_strategy") in _SKIP:
        return {"movie_results": []}

    ref_titles = state.get("reference_titles", [])
    ref_lower = {t.lower() for t in ref_titles}

    if ref_titles:
        search_hits = await tmdb.search_movies(ref_titles[0])
        if search_hits:
            ref_id = search_hits[0].get("tmdb_id")
            results = await tmdb.get_movie_recommendations(ref_id)
        else:
            results = []
    else:
        results = []

    results = [r for r in results if r.get("title", "").lower() not in ref_lower]

    return {"movie_results": results}
