from app.agents.state import AgentState
from app.services.book_service import books

_SKIP = {"movie_only", "series_only", "screen_only"}


async def book_search_node(state: AgentState) -> dict:
    if state.get("search_strategy") in _SKIP:
        return {"book_results": []}

    intent = state.get("user_intent", {})
    ref_titles = state.get("reference_titles", [])

    query = intent.get("query", "") or (ref_titles[0] if ref_titles else "")
    if not query:
        return {"book_results": []}

    try:
        results = await books.search_books(query)
    except Exception:
        return {"book_results": []}

    if ref_titles:
        ref_lower = {t.lower() for t in ref_titles}
        results = [r for r in results if r.get("title", "").lower() not in ref_lower]

    return {"book_results": results}
