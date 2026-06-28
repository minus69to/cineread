from app.agents.state import AgentState
from app.services.rag_service import rag


async def rag_search_node(state: AgentState) -> dict:
    intent = state.get("user_intent", {})
    ref_titles = state.get("reference_titles", [])
    strategy = state.get("search_strategy", "any")

    # Build semantic query from intent, NOT from the literal reference title
    vibe = intent.get("vibe", "")
    mood = intent.get("mood", "")
    query = intent.get("query", "")
    if vibe or mood:
        query = f"{query} {vibe} {mood}".strip()
    if not query:
        return {"rag_results": []}

    n = 8  # fetch extra so we have room after filtering
    if strategy in ("movie_only", "screen_only"):
        results = await rag.search_by_type(query, "movie", n_results=n)
    elif strategy == "series_only":
        results = await rag.search_by_type(query, "series", n_results=n)
    elif strategy == "book_only":
        results = await rag.search_by_type(query, "book", n_results=n)
    else:
        results = await rag.search_all(query, n_results=n)

    # Exclude titles the user already watched/read
    if ref_titles:
        ref_lower = {t.lower() for t in ref_titles}
        results = [
            r for r in results
            if r.get("metadata", {}).get("title", "").lower() not in ref_lower
        ]

    return {"rag_results": results}
