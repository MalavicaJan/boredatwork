// Single source of truth for the API origin. Set VITE_API_URL in
// .env.production so the deployed build does not point at localhost.
export const API_BASE_URL =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";
