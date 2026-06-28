import json

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from sqlalchemy import desc, select

from app.database import AsyncSessionLocal
from app.models.media_history import MediaHistory
from app.models.media_list import SavedItem

MAX_HISTORY_TURNS = 4  # last 4 user↔assistant pairs = 8 messages


async def get_history(session_id: str) -> list[BaseMessage]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MediaHistory)
            .where(MediaHistory.session_id == session_id)
            .order_by(desc(MediaHistory.created_at))
            .limit(MAX_HISTORY_TURNS)
        )
        rows = result.scalars().all()

    messages: list[BaseMessage] = []
    for row in reversed(rows):  # oldest first
        messages.append(HumanMessage(content=row.user_message))
        messages.append(AIMessage(content=row.assistant_response))
    return messages


async def save_turn(
    session_id: str,
    user_id: int,
    user_msg: str,
    assistant_msg: str,
    recommended_ids: list[str] | None = None,
) -> None:
    async with AsyncSessionLocal() as db:
        entry = MediaHistory(
            user_id=user_id,
            session_id=session_id,
            user_message=user_msg,
            assistant_response=assistant_msg,
            recommended_ids=json.dumps(recommended_ids or []),
        )
        db.add(entry)
        await db.commit()


async def build_taste_profile(user_id: int) -> str:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(SavedItem)
            .where(SavedItem.user_id == user_id)
            .order_by(desc(SavedItem.saved_at))
            .limit(30)
        )
        items = result.scalars().all()

    if not items:
        return ""

    highly_rated = [i for i in items if i.user_rating and i.user_rating >= 4.0]
    liked_types = list({i.media_type for i in items})

    lines = [f"Saved {len(items)} items across: {', '.join(liked_types)}"]
    if highly_rated:
        lines.append(f"Highly rated (4+): {', '.join(i.title for i in highly_rated[:8])}")
    if items:
        lines.append(f"Recently saved: {', '.join(i.title for i in items[:6])}")

    summary = "\n".join(lines)

    from app.agents.llm import get_llm
    from langchain_core.messages import HumanMessage as LCHumanMessage

    prompt = f"""Based on this user's media history:
{summary}

Write ONE concise sentence describing their taste profile to guide future recommendations.
Example: "User enjoys psychological thrillers and Korean cinema; prefers dark, mind-bending narratives over light entertainment."
Return only the sentence."""

    try:
        resp = await get_llm(temperature=0).ainvoke([LCHumanMessage(content=prompt)])
        return resp.content.strip()
    except Exception:
        return f"User enjoys {', '.join(liked_types)} content."
