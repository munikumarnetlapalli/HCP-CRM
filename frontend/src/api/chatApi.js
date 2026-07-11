import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

export async function postChat({ message, form_state, history }) {
  const { data } = await client.post("/api/chat", {
    message,
    form_state,
    history,
  });
  return data;
}
