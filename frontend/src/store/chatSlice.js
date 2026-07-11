import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { postChat } from "../api/chatApi";
import { setFormState } from "./formSlice";

const WELCOME = {
  role: "assistant",
  content:
    'Log interaction details here (e.g., "Met Dr. Smith, discussed Prodo-X efficacy, positive sentiment, shared brochure") or ask for help.',
};

export const sendMessage = createAsyncThunk(
  "chat/sendMessage",
  async (message, { getState, dispatch, rejectWithValue }) => {
    const state = getState();
    const history = state.chat.messages
      .filter((m) => m.role === "user" || m.role === "assistant")
      .map((m) => ({ role: m.role, content: m.content }));

    try {
      const data = await postChat({
        message,
        form_state: state.form,
        history,
      });
      dispatch(setFormState(data.form_state));
      return { reply: data.reply, tools_used: data.tools_used || [] };
    } catch (err) {
      return rejectWithValue(
        err?.response?.data?.detail || err.message || "Something went wrong talking to the AI Assistant."
      );
    }
  }
);

const chatSlice = createSlice({
  name: "chat",
  initialState: {
    messages: [WELCOME],
    isLoading: false,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state, action) => {
        state.isLoading = true;
        state.error = null;
        state.messages.push({ role: "user", content: action.meta.arg });
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.isLoading = false;
        state.messages.push({
          role: "assistant",
          content: action.payload.reply,
          success: action.payload.tools_used.length > 0,
        });
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
        state.messages.push({
          role: "assistant",
          content: `⚠️ ${action.payload}`,
          isError: true,
        });
      });
  },
});

export default chatSlice.reducer;
