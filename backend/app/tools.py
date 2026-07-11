"""
The five LangGraph tools that drive the "Log HCP Interaction" screen.

Each tool is a plain @tool function that receives the current graph
state via `InjectedState` and returns a `Command` that patches
`form_state` (which the frontend renders on the left-hand panel) plus a
`ToolMessage` that gets appended to the conversation so the LLM can
compose a natural-language confirmation.
"""
from typing import List, Optional, Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command


def _clean_list(items: Optional[List[str]]) -> List[str]:
    if not items:
        return []
    return [i.strip() for i in items if i and i.strip()]


# ---------------------------------------------------------------------------
# Tool 1: Log Interaction
# ---------------------------------------------------------------------------
@tool
def log_interaction(
    hcp_name: str,
    interaction_type: str,
    date: str,
    time: str,
    sentiment: str,
    topics_discussed: str,
    materials_shared: List[str],
    attendees: List[str],
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict, InjectedState],
) -> Command:
    """Create/populate a brand-new HCP interaction log from a natural
    language description of a field visit or call.

    Use this the FIRST time in the conversation the user describes an
    interaction, e.g. "Today I met with Dr. Smith and discussed product X
    efficiency. The sentiment was positive, and I shared the brochures."

    Extract these entities from the user's message:
    - hcp_name: the healthcare professional's name (keep any title, e.g. "Dr. Smith")
    - interaction_type: one of "Meeting", "Call", "Email", "Conference" (default "Meeting")
    - date: resolve relative dates like "today"/"yesterday" against the
      current date given in the system prompt, formatted YYYY-MM-DD
    - time: HH:MM AM/PM, use the current time if not mentioned
    - sentiment: "Positive", "Neutral", or "Negative"
    - topics_discussed: a short, professional one-line summary of what was discussed
    - materials_shared: list of brochures/samples/materials explicitly mentioned
    - attendees: list of people present (include the HCP if named as attending)

    Leave a field as an empty string / empty list only if it truly cannot
    be inferred from the message.
    """
    current = dict(state.get("form_state", {}))
    new_form = {
        **current,
        "hcp_name": hcp_name or current.get("hcp_name", ""),
        "interaction_type": interaction_type or current.get("interaction_type", "Meeting"),
        "date": date or current.get("date", ""),
        "time": time or current.get("time", ""),
        "sentiment": sentiment or current.get("sentiment", ""),
        "topics_discussed": topics_discussed or current.get("topics_discussed", ""),
        "materials_shared": _clean_list(materials_shared) or current.get("materials_shared", []),
        "attendees": _clean_list(attendees) or current.get("attendees", []),
    }
    summary = (
        f"Logged interaction with {new_form.get('hcp_name') or 'the HCP'} "
        f"({new_form.get('interaction_type', 'Meeting')}) on {new_form.get('date')}."
    )
    return Command(
        update={
            "form_state": new_form,
            "tools_used": state.get("tools_used", []) + ["log_interaction"],
            "messages": [ToolMessage(content=summary, tool_call_id=tool_call_id)],
        }
    )


# ---------------------------------------------------------------------------
# Tool 2: Edit Interaction
# ---------------------------------------------------------------------------
@tool
def edit_interaction(
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict, InjectedState],
    hcp_name: Optional[str] = None,
    interaction_type: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    sentiment: Optional[str] = None,
    topics_discussed: Optional[str] = None,
    attendees: Optional[List[str]] = None,
) -> Command:
    """Correct/modify ONE OR MORE fields of an interaction that is already
    on the form, leaving every other field untouched.

    Use this when the user is fixing a mistake in an already-logged
    interaction, e.g. "Sorry, the name was actually Dr. John and the
    sentiment was negative." Only pass the arguments for fields that should
    actually change; omit (leave as None) anything that should stay the
    same. Do NOT use this tool to create the first log of an interaction -
    use log_interaction for that.
    """
    current = dict(state.get("form_state", {}))
    changed = {}
    for field, value in {
        "hcp_name": hcp_name,
        "interaction_type": interaction_type,
        "date": date,
        "time": time,
        "sentiment": sentiment,
        "topics_discussed": topics_discussed,
        "attendees": _clean_list(attendees) if attendees is not None else None,
    }.items():
        if value is not None and value != "":
            changed[field] = value

    new_form = {**current, **changed}
    if changed:
        details = ", ".join(f"{k.replace('_', ' ')} -> {v}" for k, v in changed.items())
        summary = f"Updated fields: {details}."
    else:
        summary = "No matching fields found to update."

    return Command(
        update={
            "form_state": new_form,
            "tools_used": state.get("tools_used", []) + ["edit_interaction"],
            "messages": [ToolMessage(content=summary, tool_call_id=tool_call_id)],
        }
    )


# ---------------------------------------------------------------------------
# Tool 3: Add Material Shared / Sample Distributed
# ---------------------------------------------------------------------------
@tool
def add_material_shared(
    material_name: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict, InjectedState],
) -> Command:
    """Add a single new material, brochure, or sample to the "Materials
    Shared / Samples Distributed" list on the form, without affecting any
    other field.

    Use this when the user mentions sharing/handing out ONE additional
    item after the interaction has already been logged, e.g. "I also gave
    him a Prodo-X sample" or "Add the dosage chart to materials shared."
    If the item is already present, do not duplicate it.
    """
    current = dict(state.get("form_state", {}))
    materials = list(current.get("materials_shared", []))
    name = material_name.strip()
    if name and name.lower() not in [m.lower() for m in materials]:
        materials.append(name)
        summary = f"Added '{name}' to Materials Shared."
    else:
        summary = f"'{name}' is already listed in Materials Shared."
    new_form = {**current, "materials_shared": materials}
    return Command(
        update={
            "form_state": new_form,
            "tools_used": state.get("tools_used", []) + ["add_material_shared"],
            "messages": [ToolMessage(content=summary, tool_call_id=tool_call_id)],
        }
    )


# ---------------------------------------------------------------------------
# Tool 4: Summarize From Voice Note
# ---------------------------------------------------------------------------
@tool
def summarize_voice_note(
    voice_note_text: str,
    summary: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict, InjectedState],
) -> Command:
    """Summarize a raw voice-note transcript (dictated by the field rep)
    into a concise "Topics Discussed" entry.

    Use this when the user pastes/dictates a longer, unstructured chunk of
    text and asks you to summarize it for the Topics Discussed field
    (mirrors the "Summarize from Voice Note" action in the UI).

    Args:
        voice_note_text: the raw transcript the user provided.
        summary: YOUR concise, professional 1-3 sentence rewrite of the
            transcript suitable for a CRM record. Always fill this in
            yourself - never leave it equal to the raw transcript.
    """
    current = dict(state.get("form_state", {}))
    new_form = {**current, "topics_discussed": summary}
    return Command(
        update={
            "form_state": new_form,
            "tools_used": state.get("tools_used", []) + ["summarize_voice_note"],
            "messages": [
                ToolMessage(content="Voice note summarized into Topics Discussed.", tool_call_id=tool_call_id)
            ],
        }
    )


# ---------------------------------------------------------------------------
# Tool 5: Schedule Follow-up
# ---------------------------------------------------------------------------
@tool
def schedule_followup(
    action: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict, InjectedState],
    date: Optional[str] = None,
    notes: Optional[str] = None,
) -> Command:
    """Schedule/record a follow-up action for this HCP (e.g. a follow-up
    meeting, sending more literature, or a call-back), typically suggested
    proactively right after an interaction is logged.

    Args:
        action: short description of the follow-up, e.g. "Schedule follow-up meeting"
        date: YYYY-MM-DD if the user gave or implied a date, else None
        notes: any extra context for the follow-up
    """
    current = dict(state.get("form_state", {}))
    followup = {"action": action, "date": date, "notes": notes}
    new_form = {**current, "followup": followup}
    when = f" for {date}" if date else ""
    summary = f"Follow-up scheduled: {action}{when}."
    return Command(
        update={
            "form_state": new_form,
            "tools_used": state.get("tools_used", []) + ["schedule_followup"],
            "messages": [ToolMessage(content=summary, tool_call_id=tool_call_id)],
        }
    )


ALL_TOOLS = [
    log_interaction,
    edit_interaction,
    add_material_shared,
    summarize_voice_note,
    schedule_followup,
]
