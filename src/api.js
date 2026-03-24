import axios from "axios"

/** Same-origin /api (Vite proxy in dev) or full origin in production */
const API_BASE = import.meta.env.VITE_API_URL || "/api"

export const api = axios.create({
  baseURL: API_BASE.replace(/\/$/, ""),
  headers: { "Content-Type": "application/json" },
})

export function getApiBase() {
  return API_BASE.replace(/\/$/, "")
}
