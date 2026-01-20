import axios from "axios";

// Always call the API directly (no nginx proxy). Prefer explicit env, fall back to prod URL.
export const API_BASE_URL = (import.meta as any).env.API_BASE_URL || "https://sessions-api.tuhuratech.org.nz";

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  withCredentials: true, // Important for cookie-based auth
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      // Redirect to login on unauthorized or forbidden
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

export default api;
