import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return { Authorization: `Bearer ${token}` };
};

export const login = (email, password) =>
  axios.post(`${API_BASE}/auth/login`, { email, password });

export const register = (email, username, password) =>
  axios.post(`${API_BASE}/auth/signup`, { email, username, password });

export const getChats = () =>
  axios.get(`${API_BASE}/auth/conversations`, { headers: getAuthHeaders() });

export const startNewChat = () =>
  axios.post(`${API_BASE}/auth/conversations`, {}, { headers: getAuthHeaders() });

export const sendMessage = (conversation_id, content) =>
  axios.post(`${API_BASE}/auth/messages`, { conversation_id, content }, { headers: getAuthHeaders() });
