"""LangGraph graph state definition."""
from typing import TypedDict, List, Annotated
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    form_state: dict
    tools_used: List[str]
