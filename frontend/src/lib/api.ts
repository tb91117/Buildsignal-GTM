// In local dev, Vite proxies these paths to the FastAPI backend (see vite.config.ts).
// In production, set VITE_API_BASE_URL to the deployed backend's origin
// (e.g. https://api.buildsignal.example.com) since a static Vercel deploy
// has no backend of its own to proxy to.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? ""

export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`
}
