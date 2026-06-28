import json
import re

from langchain_core.messages import HumanMessage

from app.agents.llm import get_llm
from app.agents.state import AgentState

_PROMPT = """You are an expert in literature, film, and television.

The user referenced: {reference_titles}

Find thematically connected works across ALL media types by reasoning about:
- Core themes (isolation, identity, power, survival, grief, hope)
- Narrative style (non-linear, unreliable narrator, slow burn, anthology)
- Emotional tone (dark, hopeful, tense, melancholic, mind-bending)
- World-building (grounded, dystopian, fantastical, sci-fi)

Available candidates:
MOVIES: {movies}
SERIES: {series}
BOOKS: {books}

For each strong thematic connection, explain the bridge briefly.
Example: "If you loved Dark's time paradox and family drama, Devs delivers the same philosophical dread through quantum computing."

Return ONLY valid JSON:
{{
  "cross_media_connections": [
    {{
      "id": "movie_27205",
      "title": "Inception",
      "media_type": "movie",
      "reasoning": "Shares the same mind-bending layered reality structure..."
    }}
  ]
}}"""



def _parse(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    return json.loads(text)


def _summarise(items: list[dict], n: int = 8) -> str:
    return json.dumps(
        [{"id": i.get("id"), "title": i.get("title"), "overview": i.get("overview", "")[:150]}
         for i in items[:n]],
        ensure_ascii=False,
    )


async def cross_media_node(state: AgentState) -> dict:
    if not state.get("is_cross_media") and not state.get("reference_titles"):
        return {"cross_media_connections": []}

    ref = state.get("reference_titles", [])
    movies = state.get("movie_results", [])
    series = state.get("series_results", [])
    books = state.get("book_results", [])
    rag = state.get("rag_results", [])

    # Merge RAG results into the candidate pools
    for r in rag:
        meta = r.get("metadata", {})
        t = meta.get("type", "")
        candidate = {
            "id": r["id"],
            "title": meta.get("title", ""),
            "overview": r.get("document", "")[:200],
            "media_type": t,
        }
        if t == "movie":
            movies.append(candidate)
        elif t == "series":
            series.append(candidate)
        elif t == "book":
            books.append(candidate)

    if not (movies or series or books):
        return {"cross_media_connections": []}

    prompt = _PROMPT.format(
        reference_titles=", ".join(ref) if ref else "unspecified",
        movies=_summarise(movies),
        series=_summarise(series),
        books=_summarise(books),
    )

    try:
        response = await get_llm(temperature=0.4).ainvoke([HumanMessage(content=prompt)])
        result = _parse(response.content)
        return {"cross_media_connections": result.get("cross_media_connections", [])}
    except Exception:
        return {"cross_media_connections": []}
