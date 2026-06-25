import axios, { AxiosInstance, AxiosError } from "axios";
import toast from "react-hot-toast";

const BASE_URL = import.meta.env.VITE_API_URL ?? "/api/v1";

function createApiClient(): AxiosInstance {
  const client = axios.create({
    baseURL: BASE_URL,
    timeout: 15_000,
    headers: { "Content-Type": "application/json" },
  });

  // Request interceptor — inject Bearer token
  client.interceptors.request.use((config) => {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  });

  // Response interceptor — handle 401 refresh and error toasts
  client.interceptors.response.use(
    (response) => response,
    async (error: AxiosError<{ detail?: string }>) => {
      if (error.response?.status === 401) {
        const refresh = localStorage.getItem("refresh_token");
        if (refresh) {
          try {
            const { data } = await axios.post(`${BASE_URL}/auth/refresh`, null, {
              headers: { Authorization: `Bearer ${refresh}` },
            });
            localStorage.setItem("access_token", data.access_token);
            error.config!.headers!["Authorization"] = `Bearer ${data.access_token}`;
            return client.request(error.config!);
          } catch {
            localStorage.clear();
            window.location.href = "/login";
          }
        }
      }
      const message = error.response?.data?.detail ?? error.message ?? "An error occurred";
      if (error.response?.status !== 404) {
        toast.error(message);
      }
      return Promise.reject(error);
    }
  );

  return client;
}

export const api = createApiClient();
