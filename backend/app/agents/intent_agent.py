import json
import re

from langchain_core.messages import HumanMessage

from app.agents.llm import get_llm
from app.agents.state import AgentState

_PROMPT = """You are analyzing a media recommendation request. The user may write in English, Bengali, or a mix of both.

User message: {message}
Recent conversation: {history}
User taste profile: {taste_profile}

Use the taste profile (if provided) to better understand their preferences, but the current message takes priority.

Extract the following and return ONLY valid JSON — no markdown, no explanation:
{{
  "mood": "emotional tone they want (dark / hopeful / thrilling / melancholic / romantic / etc.)",
  "vibe": "themes or style (psychological thriller / sci-fi / slow burn / comedy / etc.)",
  "constraints": "any specific requirements (short series / old film / Bengali / etc.) or empty string",
  "media_preference": "movie" or "series" or "book" or "any",
  "query": "THEMATIC English phrase for semantic search — expand the reference title into its core themes, mood, style, and audience. NEVER just repeat the title. Examples: 'books like Ikigai' → 'purpose meaning mindfulness happiness Japanese philosophy inspiring self-improvement'; 'Dark er moto show' → 'time travel mystery dark thriller family secrets'; 'Dune er moto sci-fi' → 'epic space opera political intrigue desert survival world-building'"
}}"""



def _parse(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    return json.loads(text)


async def intent_node(state: AgentState) -> dict:
    messages = state["messages"]
    last = messages[-1].content if messages else ""
    history = "\n".join(
        f"{m.type}: {m.content}" for m in messages[:-1][-4:]
    )

    taste_profile = state.get("taste_profile", "")
    prompt = _PROMPT.format(message=last, history=history, taste_profile=taste_profile or "none")
    response = await get_llm(temperature=0.2).ainvoke([HumanMessage(content=prompt)])

    try:
        intent = _parse(response.content)
    except Exception:
        intent = {
            "mood": "",
            "vibe": "",
            "constraints": "",
            "media_preference": "any",
            "query": last,
        }

    return {"user_intent": intent}
