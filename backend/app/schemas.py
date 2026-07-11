"""Pydantic models shared by the FastAPI layer."""
from typing import List, Optional
from pydantic import BaseModel, Field


class FollowUp(BaseModel):
    action: str = ""
    date: Optional[str] = None
    notes: Optional[str] = None


class FormState(BaseModel):
    hcp_name: str = ""
    interaction_type: str = "Meeting"
    date: str = ""
    time: str = ""
    attendees: List[str] = Field(default_factory=list)
    topics_discussed: str = ""
    materials_shared: List[str] = Field(default_factory=list)
    sentiment: str = ""
    followup: Optional[FollowUp] = None


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    form_state: FormState
    history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    form_state: FormState
    tools_used: List[str] = Field(default_factory=list)
