/** Backend API base URLs — tried in order (Docker, then local). */
export const API_BASE_URLS = [
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api",
  "http://backend:8000/api",
  "http://127.0.0.1:8000/api",
  "http://localhost:8000/api",
].filter((url, index, arr) => arr.indexOf(url) === index);

export const TOKEN_REFRESH_PATHS = API_BASE_URLS.map(
  (base) => `${base.replace(/\/api\/?$/, "")}/api/token/refresh/`
);
