import json
import re

from langchain_core.messages import HumanMessage

from app.agents.llm import get_llm
from app.agents.state import AgentState

_PROMPT = """Analyze this media request and decide a search strategy.

User message: {message}
Extracted intent: {intent}

Search strategies:
- "movie_only"   : user explicitly wants a movie
- "series_only"  : user explicitly wants a TV series
- "book_only"    : user explicitly wants a book
- "screen_only"  : movie OR series, user doesn't specify which
- "any"          : no media preference stated
- "cross_media"  : user finished one media type and wants recommendations in ANOTHER type
                   (e.g. "just finished the book, what movie?", "series শেষ, কোনো book আছে?")

Also extract:
- reference_titles: exact titles of movies/series/books the user mentioned by name (empty list if none)
- is_cross_media: true only for "cross_media" strategy

Return ONLY valid JSON:
{{
  "search_strategy": "...",
  "reference_titles": [],
  "is_cross_media": false
}}"""



def _parse(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    return json.loads(text)


async def router_node(state: AgentState) -> dict:
    messages = state["messages"]
    last = messages[-1].content if messages else ""
    intent = state.get("user_intent", {})

    prompt = _PROMPT.format(message=last, intent=json.dumps(intent))
    response = await get_llm(temperature=0.1).ainvoke([HumanMessage(content=prompt)])

    try:
        result = _parse(response.content)
    except Exception:
        result = {
            "search_strategy": intent.get("media_preference", "any"),
            "reference_titles": [],
            "is_cross_media": False,
        }

    return {
        "search_strategy": result.get("search_strategy", "any"),
        "reference_titles": result.get("reference_titles", []),
        "is_cross_media": result.get("is_cross_media", False),
    }
