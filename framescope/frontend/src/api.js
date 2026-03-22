import axios from "axios";

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = {
  detect: (formData) => axios.post(`${BASE}/api/detect`, formData),
  getJob: (jobId) => axios.get(`${BASE}/api/jobs/${jobId}`).then((r) => r.data),
};
