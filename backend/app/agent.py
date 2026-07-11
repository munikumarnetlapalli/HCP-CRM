"""LangGraph agent wiring: Groq LLM + tool-calling loop."""
import datetime

from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .config import GROQ_API_KEY, GROQ_MODEL
from .state import AgentState
from .tools import ALL_TOOLS


def _llm():
    return ChatGroq(
        model=GROQ_MODEL,
        api_key=GROQ_API_KEY,
        temperature=0,
    ).bind_tools(ALL_TOOLS)


def _system_prompt(form_state: dict) -> str:
    today = datetime.date.today().isoformat()
    now = datetime.datetime.now().strftime("%I:%M %p")
    return f"""You are the AI Assistant embedded in an AI-first pharma CRM's
"Log HCP Interaction" screen. Field representatives describe their visits
to Healthcare Professionals (HCPs) in plain English, and you translate
that into the structured form on the left of the screen by calling tools.
You never fabricate data you were not given or cannot reasonably infer.

Today's date is {today} and the current time is {now}. Resolve any
relative dates/times ("today", "this morning", "just now") against these.

Current form state (JSON): {form_state}

Tool selection rules:
- A brand-new description of an interaction that hasn't been logged yet -> log_interaction.
- A correction to fields already on the form -> edit_interaction (only the changed fields).
- Mentioning ONE additional sample/brochure shared after logging -> add_material_shared.
- A raw/rambling voice-note transcript that needs turning into a clean
  Topics Discussed summary -> summarize_voice_note.
- A request to schedule/suggest a next step or follow-up -> schedule_followup.
- You may call more than one tool for a single message if the user asks for
  multiple things at once.

After any tool calls complete, reply with a short, warm, professional
confirmation message summarizing exactly what changed on the form. If
nothing needed a tool (e.g. the user asked a question), just answer
directly without calling a tool. Keep replies concise (2-4 sentences)."""


def agent_node(state: AgentState):
    llm = _llm()
    sys_msg = SystemMessage(content=_system_prompt(state.get("form_state", {})))
    response = llm.invoke([sys_msg] + state["messages"])
    return {"messages": [response]}


def route_after_agent(state: AgentState):
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return END


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(ALL_TOOLS))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", route_after_agent, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile()


AGENT = build_graph()
