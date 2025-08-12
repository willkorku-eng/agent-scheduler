import axios from "axios";
const apiBase = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const client = axios.create({
  baseURL: apiBase,
  headers: { "Content-Type": "application/json" },
  timeout: 60000
});
export default client;
