"""FastAPI entrypoint."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage, HumanMessage

from .agent import AGENT
from .config import GROQ_API_KEY
from .schemas import ChatRequest, ChatResponse, FormState

app = FastAPI(title="AI-First HCP CRM Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "groq_configured": bool(GROQ_API_KEY)}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is not configured. Add it to backend/.env",
        )

    messages = []
    for m in req.history:
        if m.role == "user":
            messages.append(HumanMessage(content=m.content))
        else:
            messages.append(AIMessage(content=m.content))
    messages.append(HumanMessage(content=req.message))

    initial_state = {
        "messages": messages,
        "form_state": req.form_state.model_dump(),
        "tools_used": [],
    }

    try:
        result = AGENT.invoke(initial_state)
    except Exception as exc:  # surfaced to the frontend chat as an error bubble
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc

    ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage) and m.content]
    reply = ai_messages[-1].content if ai_messages else "Done."

    return ChatResponse(
        reply=reply,
        form_state=FormState(**result["form_state"]),
        tools_used=result.get("tools_used", []),
    )
