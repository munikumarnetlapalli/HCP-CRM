# AI-First CRM — HCP Log Interaction Screen

An AI-first "Log HCP Interaction" screen for pharma field representatives.
The screen is a split view: a **structured form** on the left and a
**conversational AI Assistant** on the right. Instead of clicking through
the form, the rep can just describe what happened in plain English — a
**LangGraph agent** running on **Groq (`gemma2-9b-it`)** parses the message,
calls the right tool(s), and the form on the left updates itself in real
time.

```
"Today I met with Dr. Smith and discussed product X efficiency.
 The sentiment was positive, and I shared the brochures."
        │
        ▼
┌───────────────────┐        ┌──────────────────────────┐
│  React + Redux UI  │──POST──▶│  FastAPI  /api/chat      │
│  (left: form)      │◀────────│  LangGraph agent + Groq  │
│  (right: chat)      │  JSON   │  5 tools                 │
└───────────────────┘        └──────────────────────────┘
```

## Why LangGraph

The agent is modeled as an explicit `StateGraph` with two nodes:

- **`agent`** — calls the Groq LLM (bound to all 5 tools) with the
  conversation history + the current form state serialized into the system
  prompt, so the model always knows what's already on the form and never
  overwrites fields it wasn't asked to change.
- **`tools`** — a `ToolNode` that executes whichever tool(s) the LLM chose.

A conditional edge loops `agent → tools → agent` until the model responds
with plain text (no more tool calls), then the graph ends. Every tool
returns a LangGraph `Command` that patches the graph's `form_state`, so the
"database" for a turn is just the state object flowing through the graph —
no hidden global mutation, fully inspectable, and easy to persist or
checkpoint later.

## The 5 LangGraph Tools

| # | Tool | Purpose | Example user message |
|---|------|---------|----------------------|
| 1 | `log_interaction` | Creates a brand-new interaction log from a free-text description (entity extraction: HCP name, type, date/time, sentiment, topics, materials, attendees). | *"Today I met with Dr. Smith and discussed product X efficiency. The sentiment was positive, and I shared the brochures."* |
| 2 | `edit_interaction` | Updates **only** the fields mentioned, leaving everything else untouched. | *"Sorry, the name was actually Dr. John and the sentiment was negative."* |
| 3 | `add_material_shared` | Appends a single sample/brochure to Materials Shared without touching other fields. | *"I also gave him a Prodo-X sample."* |
| 4 | `summarize_voice_note` | Turns a raw, rambling voice-note transcript into a clean "Topics Discussed" summary (mirrors the "Summarize from Voice Note" UI action). | *"Summarize this voice note: uh so I went in, talked about pricing, he seemed unsure, said call back next week..."* |
| 5 | `schedule_followup` | Records a suggested/requested follow-up action (e.g. schedule next meeting). | *"Yes, schedule a follow-up meeting for next Tuesday."* |

All tools use the `InjectedState` + `Command` pattern so they can read and
patch the shared `form_state` directly instead of returning free text the
backend would have to re-parse.

## Tech Stack

- **Frontend:** React 18 + Redux Toolkit (Vite)
- **Backend:** Python + FastAPI
- **AI Agent Framework:** LangGraph
- **LLM:** Groq `gemma2-9b-it` (via `langchain-groq`)
- **Font:** Google Inter

## Project Structure

```
hcp-crm/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, /api/chat endpoint
│   │   ├── agent.py         # LangGraph graph (agent + tools nodes)
│   │   ├── tools.py         # The 5 LangGraph tools
│   │   ├── state.py         # AgentState TypedDict
│   │   ├── schemas.py       # Pydantic request/response models
│   │   └── config.py        # Env var loading
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── store/            # Redux: formSlice, chatSlice, store
    │   ├── components/       # LogInteractionForm, AIAssistantChat
    │   ├── api/chatApi.js     # Axios client for /api/chat
    │   ├── App.jsx / main.jsx
    │   └── index.css          # Theme (matches the provided mock)
    ├── package.json
    └── .env.example
```

## Running Locally

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# then edit .env and paste your Groq API key from https://console.groq.com
uvicorn app.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/api/health`

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env   # defaults to http://localhost:8000, adjust if needed
npm run dev
```

Open `http://localhost:5173`. The left panel is the structured form (you
can also edit it by hand — the screen supports both entry modes); the
right panel is the AI Assistant. Type a message and hit **Log** (or
Enter) to drive the form through the agent.

### Try it

1. `Today I met with Dr. Smith and discussed product X efficiency. The sentiment was positive, and I shared the brochures.` → `log_interaction`
2. `Sorry, the name was actually Dr. John and the sentiment was negative.` → `edit_interaction`
3. `I also handed him a dosage chart sample.` → `add_material_shared`
4. `Summarize this voice note: uh met the doctor, talked pricing, he wants a callback next week` → `summarize_voice_note`
5. `Can you schedule a follow-up meeting for next week?` → `schedule_followup`

## Notes

- The LLM is always given the **current form state** and **today's date**
  in the system prompt, so relative dates ("today", "yesterday") and
  partial edits resolve correctly and previously-filled fields are never
  silently blanked out.
- The frontend never fills the form itself — every field mutation from
  chat comes back from the backend as the authoritative new `form_state`,
  which is written into Redux via `setFormState`. Manual typing in the
  form dispatches the same slice's `setField`, so both entry paths share
  one source of truth.
