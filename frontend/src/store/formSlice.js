import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  hcp_name: "",
  interaction_type: "Meeting",
  date: "",
  time: "",
  attendees: [],
  topics_discussed: "",
  materials_shared: [],
  sentiment: "",
  followup: null,
};

const formSlice = createSlice({
  name: "form",
  initialState,
  reducers: {
    // Manual edits from the structured form (left panel inputs)
    setField(state, action) {
      const { field, value } = action.payload;
      state[field] = value;
    },
    addAttendee(state, action) {
      const name = action.payload?.trim();
      if (name && !state.attendees.includes(name)) state.attendees.push(name);
    },
    removeAttendee(state, action) {
      state.attendees = state.attendees.filter((a) => a !== action.payload);
    },
    addMaterial(state, action) {
      const name = action.payload?.trim();
      if (name && !state.materials_shared.some((m) => m.toLowerCase() === name.toLowerCase())) {
        state.materials_shared.push(name);
      }
    },
    removeMaterial(state, action) {
      state.materials_shared = state.materials_shared.filter((m) => m !== action.payload);
    },
    // Full replace, used when the AI agent returns an updated form_state
    setFormState(_state, action) {
      return { ...initialState, ...action.payload };
    },
    resetForm() {
      return initialState;
    },
  },
});

export const {
  setField,
  addAttendee,
  removeAttendee,
  addMaterial,
  removeMaterial,
  setFormState,
  resetForm,
} = formSlice.actions;

export default formSlice.reducer;
