import axios from 'axios';

export const api = axios.create({
  // Use relative path so Vite proxy can handle it
  baseURL: '/api',
  timeout: 5000,
});

// Add request interceptor for auth if needed
api.interceptors.request.use((config) => {
  // You can add auth token here if required
  return config;
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
); 