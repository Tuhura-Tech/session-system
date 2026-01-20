import axios from "axios";

// In production, use relative URL so nginx can proxy to backend
// In development, use localhost
const API_BASE_URL =
  (import.meta as any).env.VITE_API_URL || 
  (import.meta as any).env.MODE === 'production' ? '' : 'http://localhost:8000';

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
