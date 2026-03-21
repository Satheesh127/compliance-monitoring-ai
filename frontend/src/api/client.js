import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
});

export async function fetchUpdates() {
  const response = await api.get("/api/updates");
  return response.data;
}

export async function fetchStats() {
  const response = await api.get("/api/stats");
  return response.data;
}

export async function askChatbot(question) {
  const response = await api.post("/api/chat", { question });
  return response.data;
}
