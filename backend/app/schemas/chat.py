from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    items: list[dict] = []
    session_id: str
