import json

from langchain_core.messages import HumanMessage

from app.agents.llm import get_llm
from app.agents.state import AgentState

_BADGES = {"movie": "🎬", "series": "📺", "book": "📚"}

_PROMPT = """You are CineRead, a friendly cross-media recommendation assistant.
You understand English and Bengali — respond naturally in the same language the user used.

User's request: {message}
Their mood/vibe: {mood} / {vibe}
User taste profile: {taste_profile}

Recommendations to present:
{items}

Write a warm, conversational response that:
1. Acknowledges what they referenced (1 sentence)
2. Introduces the recommendations naturally (not as a numbered list)
3. For each item, mention the media type badge, title, year, rating, and ONE sentence on WHY it fits
4. If there's a cross-media connection (book↔movie↔series), highlight it explicitly
5. If the taste profile reveals strong preferences, briefly acknowledge the match

Keep it concise — 3 to 5 recommendations max. Use the user's language."""



def _format_items(items: list[dict]) -> str:
    lines = []
    for item in items:
        badge = _BADGES.get(item.get("media_type", ""), "")
        rating = f"⭐{item['rating']}" if item.get("rating") else ""
        year = f"({item['year']})" if item.get("year") else ""
        reasoning = item.get("reasoning", "")
        lines.append(
            f"{badge} {item.get('media_type','').upper()} | {item.get('title','')} {year} {rating}\n"
            f"Creator: {item.get('creator','')}\n"
            f"Overview: {item.get('overview','')[:200]}\n"
            f"Why: {reasoning}"
        )
    return "\n\n".join(lines)


async def response_node(state: AgentState) -> dict:
    messages = state["messages"]
    last = messages[-1].content if messages else ""
    intent = state.get("user_intent", {})
    ranked = state.get("ranked_items", [])

    if not ranked:
        return {"response": "Sorry, I couldn't find good recommendations for that. Could you give me more details about what you're looking for?"}

    taste_profile = state.get("taste_profile", "")
    prompt = _PROMPT.format(
        message=last,
        mood=intent.get("mood", ""),
        vibe=intent.get("vibe", ""),
        taste_profile=taste_profile or "none",
        items=_format_items(ranked),
    )

    try:
        response = await get_llm(temperature=0.6).ainvoke([HumanMessage(content=prompt)])
        return {"response": response.content}
    except Exception as e:
        fallback = "\n\n".join(
            f"{_BADGES.get(i.get('media_type',''), '')} **{i.get('title','')}** ({i.get('year','')}) ⭐{i.get('rating','')}\n{i.get('overview','')[:150]}"
            for i in ranked
        )
        return {"response": fallback}
