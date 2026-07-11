import { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { sendMessage } from "../store/chatSlice.js";

function bubbleClass(msg) {
  if (msg.role === "user") return "bubble user";
  if (msg.isError) return "bubble error";
  if (msg.success) return "bubble success";
  return "bubble info";
}

export default function AIAssistantChat() {
  const dispatch = useDispatch();
  const { messages, isLoading } = useSelector((s) => s.chat);
  const [draft, setDraft] = useState("");
  const listRef = useRef(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isLoading]);

  const submit = () => {
    const text = draft.trim();
    if (!text || isLoading) return;
    dispatch(sendMessage(text));
    setDraft("");
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <section className="panel chat-panel">
      <div className="chat-header">
        <div className="ai-badge">🤖</div>
        <h2>AI Assistant</h2>
      </div>
      <p className="chat-subtitle">Log Interaction details here via chat</p>
      <hr className="chat-divider" />

      <div className="chat-messages" ref={listRef}>
        {messages.map((m, i) => (
          <div key={i} className={bubbleClass(m)}>
            {m.role === "assistant" && m.success ? "✅ " : ""}
            {m.content}
          </div>
        ))}
        {isLoading && <div className="bubble thinking">Thinking…</div>}
      </div>

      <div className="chat-input-row">
        <textarea
          placeholder="Describe Interaction..."
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKeyDown}
          rows={1}
        />
        <button className="btn-log" onClick={submit} disabled={isLoading}>
          🤖<span>Log</span>
        </button>
      </div>
    </section>
  );
}
