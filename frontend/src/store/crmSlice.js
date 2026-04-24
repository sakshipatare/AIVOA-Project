import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

const API_BASE = 'http://localhost:8001';

export const fetchHCPs = createAsyncThunk('crm/fetchHCPs', async () => {
  const response = await axios.get(`${API_BASE}/hcps`);
  return response.data;
});

export const sendMessage = createAsyncThunk('crm/sendMessage', async ({ message, hcpId }, { getState }) => {
  const { chatHistory } = getState().crm;
  const response = await axios.post(`${API_BASE}/chat`, { 
    message, 
    hcp_id: hcpId,
  history: chatHistory.slice(-4).map(m => ({ role: m.role, content: m.content }))
  });
  return { message, response: response.data.response };
});

const crmSlice = createSlice({
  name: 'crm',
  initialState: {
    hcps: [],
    selectedHcp: null,
    chatHistory: [],
    loading: false,
    status: 'idle',
  },
  reducers: {
    setSelectedHcp: (state, action) => {
      state.selectedHcp = action.payload;
      state.chatHistory = []; // Reset chat for new HCP
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchHCPs.fulfilled, (state, action) => {
        state.hcps = action.payload;
        if (action.payload.length > 0 && !state.selectedHcp) {
          state.selectedHcp = action.payload[0];
        }
      })
      .addCase(sendMessage.pending, (state) => {
        state.loading = true;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.loading = false;
        state.chatHistory.push({ role: 'user', content: action.payload.message });
        state.chatHistory.push({ role: 'ai', content: action.payload.response });
      });
  },
});

export const { setSelectedHcp } = crmSlice.actions;
export default crmSlice.reducer;
