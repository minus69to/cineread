from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str

    # Personalization
    taste_profile: str       # LLM-built summary of user's taste from saved/rated items

    # Intent
    user_intent: dict        # mood, vibe, constraints, media_preference, query
    reference_titles: list[str]
    is_cross_media: bool
    search_strategy: str     # movie_only / series_only / book_only / screen_only / any / cross_media

    # Raw search results
    movie_results: list[dict]
    series_results: list[dict]
    book_results: list[dict]
    rag_results: list[dict]

    # Cross-media reasoning
    cross_media_connections: list[dict]

    # Final output
    ranked_items: list[dict]
    response: str
