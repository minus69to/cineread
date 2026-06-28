import json

from fastapi import APIRouter, Header
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.agents.graph import agent_graph
from app.schemas.chat import ChatRequest
from app.services.memory_service import build_taste_profile, get_history, save_turn

router = APIRouter(prefix="/chat", tags=["chat"])

_EMPTY_STATE = {
    "taste_profile": "",
    "user_intent": {},
    "reference_titles": [],
    "is_cross_media": False,
    "search_strategy": "any",
    "movie_results": [],
    "series_results": [],
    "book_results": [],
    "rag_results": [],
    "cross_media_connections": [],
    "ranked_items": [],
    "response": "",
}


def _parse_user_id(authorization: str | None) -> int | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    from jose import jwt, JWTError
    from app.config import settings
    try:
        token = authorization.removeprefix("Bearer ").strip()
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return int(payload["sub"])
    except (JWTError, Exception):
        return None


@router.post("")
async def chat(req: ChatRequest, authorization: str | None = Header(default=None)):
    user_id = _parse_user_id(authorization)

    # Load conversation history and taste profile in parallel
    history = await get_history(req.session_id)
    taste_profile = await build_taste_profile(user_id) if user_id else ""

    async def event_stream():
        initial_state = {
            **_EMPTY_STATE,
            "messages": [*history, HumanMessage(content=req.message)],
            "session_id": req.session_id,
            "taste_profile": taste_profile,
        }

        final_response = ""
        final_items: list[dict] = []

        try:
            async for chunk in agent_graph.astream(initial_state):
                if "ranking" in chunk:
                    items = chunk["ranking"].get("ranked_items", [])
                    if items:
                        final_items = items
                        yield f"data: {json.dumps({'type': 'media', 'items': items})}\n\n"

                if "responder" in chunk:
                    text = chunk["responder"].get("response", "")
                    if text:
                        final_response = text
                        yield f"data: {json.dumps({'type': 'text', 'content': text})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        yield "data: [DONE]\n\n"

        # Persist this turn after stream closes
        if final_response:
            recommended_ids = [i.get("id", "") for i in final_items]
            await save_turn(
                session_id=req.session_id,
                user_id=user_id or 0,
                user_msg=req.message,
                assistant_msg=final_response,
                recommended_ids=recommended_ids,
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
