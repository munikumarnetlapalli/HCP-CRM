import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  setField,
  addAttendee,
  removeAttendee,
  addMaterial,
  removeMaterial,
} from "../store/formSlice.js";

const INTERACTION_TYPES = ["Meeting", "Call", "Email", "Conference"];
const SENTIMENTS = [
  { key: "Positive", cls: "positive" },
  { key: "Neutral", cls: "neutral" },
  { key: "Negative", cls: "negative" },
];

export default function LogInteractionForm() {
  const dispatch = useDispatch();
  const form = useSelector((s) => s.form);

  const [attendeeInput, setAttendeeInput] = useState("");
  const [materialInput, setMaterialInput] = useState("");

  const onFieldChange = (field) => (e) =>
    dispatch(setField({ field, value: e.target.value }));

  const submitAttendee = (e) => {
    if (e.key === "Enter" && attendeeInput.trim()) {
      e.preventDefault();
      dispatch(addAttendee(attendeeInput));
      setAttendeeInput("");
    }
  };

  const submitMaterial = () => {
    if (materialInput.trim()) {
      dispatch(addMaterial(materialInput));
      setMaterialInput("");
    }
  };

  return (
    <section className="panel form-panel">
      <h1 className="panel-title">Log HCP Interaction</h1>

      <h3 className="section-label">Interaction Details</h3>

      <div className="field-row">
        <div className="field">
          <label>HCP Name</label>
          <input
            type="text"
            placeholder="e.g. Dr. Smith"
            value={form.hcp_name}
            onChange={onFieldChange("hcp_name")}
          />
        </div>
        <div className="field">
          <label>Interaction Type</label>
          <select value={form.interaction_type} onChange={onFieldChange("interaction_type")}>
            {INTERACTION_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="field-row">
        <div className="field">
          <label>Date</label>
          <input type="date" value={form.date} onChange={onFieldChange("date")} />
        </div>
        <div className="field">
          <label>Time</label>
          <input type="time" value={form.time} onChange={onFieldChange("time")} />
        </div>
      </div>

      <div className="field" style={{ marginBottom: 18 }}>
        <label>Attendees</label>
        <div className="chip-input">
          {form.attendees.map((a) => (
            <span className="chip" key={a}>
              {a}
              <button onClick={() => dispatch(removeAttendee(a))} aria-label={`Remove ${a}`}>
                ×
              </button>
            </span>
          ))}
          <input
            type="text"
            placeholder="Enter names or search..."
            value={attendeeInput}
            onChange={(e) => setAttendeeInput(e.target.value)}
            onKeyDown={submitAttendee}
          />
        </div>
      </div>

      <div className="field">
        <label>Topics Discussed</label>
        <textarea
          placeholder="What was discussed during the interaction..."
          value={form.topics_discussed}
          onChange={onFieldChange("topics_discussed")}
        />
        <button className="voice-link" type="button" title="Ask the AI Assistant to summarize a voice note">
          🎙️ Summarize from Voice Note (Requires Consent)
        </button>
      </div>

      <h3 className="section-label">Materials Shared / Samples Distributed</h3>
      <div className="field">
        <label>Materials Shared</label>
        <div className="materials-search-row">
          <div className="chip-input" style={{ flex: 1 }}>
            {form.materials_shared.map((m) => (
              <span className="chip" key={m}>
                {m}
                <button onClick={() => dispatch(removeMaterial(m))} aria-label={`Remove ${m}`}>
                  ×
                </button>
              </span>
            ))}
            <input
              type="text"
              placeholder="Brochures, samples..."
              value={materialInput}
              onChange={(e) => setMaterialInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), submitMaterial())}
            />
          </div>
          <button className="btn-search" type="button" onClick={submitMaterial}>
            🔍 Search/Add
          </button>
        </div>
      </div>

      <h3 className="section-label">Sentiment</h3>
      <div className="sentiment-row">
        {SENTIMENTS.map(({ key, cls }) => (
          <div
            key={key}
            className={`sentiment-pill ${cls} ${form.sentiment === key ? "active " + cls : ""}`}
            onClick={() => dispatch(setField({ field: "sentiment", value: key }))}
          >
            {key}
          </div>
        ))}
      </div>

      {form.followup && (
        <div className="followup-card">
          <b>Suggested Follow-up</b>
          {form.followup.action}
          {form.followup.date ? ` — ${form.followup.date}` : ""}
          {form.followup.notes ? ` (${form.followup.notes})` : ""}
        </div>
      )}
    </section>
  );
}
