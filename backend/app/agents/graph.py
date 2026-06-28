import asyncio

from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.intent_agent import intent_node
from app.agents.media_router_agent import router_node
from app.agents.movie_search_agent import movie_search_node
from app.agents.series_search_agent import series_search_node
from app.agents.book_search_agent import book_search_node
from app.agents.rag_agent import rag_search_node
from app.agents.cross_media_agent import cross_media_node
from app.agents.ranking_agent import ranking_node
from app.agents.response_agent import response_node


async def parallel_search_node(state: AgentState) -> dict:
    """Run all four searches concurrently and merge results into state."""
    movie_res, series_res, book_res, rag_res = await asyncio.gather(
        movie_search_node(state),
        series_search_node(state),
        book_search_node(state),
        rag_search_node(state),
    )
    return {
        **movie_res,
        **series_res,
        **book_res,
        **rag_res,
    }


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("intent", intent_node)
    workflow.add_node("router", router_node)
    workflow.add_node("search", parallel_search_node)
    workflow.add_node("cross_media", cross_media_node)
    workflow.add_node("ranking", ranking_node)
    workflow.add_node("responder", response_node)

    workflow.set_entry_point("intent")
    workflow.add_edge("intent", "router")
    workflow.add_edge("router", "search")
    workflow.add_edge("search", "cross_media")
    workflow.add_edge("cross_media", "ranking")
    workflow.add_edge("ranking", "responder")
    workflow.add_edge("responder", END)

    return workflow.compile()


agent_graph = build_graph()
