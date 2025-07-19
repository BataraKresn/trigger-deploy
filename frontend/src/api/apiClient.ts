import axios from 'axios';
import useGlobalState from '@/store/globalState';

// Pastikan baseURL tidak memiliki trailing slash
const baseUrl = import.meta.env.VITE_API_URL.replace(/\/+$/, '');

export const api = axios.create({
  baseURL: baseUrl,
  timeout: 10000,
});

// Tambahkan token Authorization jika tersedia
api.interceptors.request.use(async (config) => {
  const { token, setToken } = useGlobalState.getState();
  if (token) {
    const tokenPayload = JSON.parse(atob(token.split('.')[1]));
    const exp = tokenPayload.exp * 1000; // Convert to milliseconds
    const now = Date.now();

    if (exp - now < 5 * 60 * 1000) {
      // Refresh if token expires in less than 5 minutes
      try {
        const response = await axios.post(`${baseUrl}/api/refresh-token`, { token });
        const newToken = response.data.token;
        setToken(newToken);
        config.headers.Authorization = `Bearer ${newToken}`;
      } catch (error) {
        console.error('Failed to refresh token:', error);
        useGlobalState.getState().logout();
      }
    } else {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Tangani error global
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Tangani error berdasarkan status code
      switch (error.response.status) {
        case 401:
          // Token tidak valid atau telah kedaluwarsa
          useGlobalState.getState().logout();
          break;
        case 403:
          // Akses ditolak
          console.error('Akses ditolak:', error.response.data);
          break;
        default:
          console.error('Terjadi kesalahan:', error.response.data);
      }
    } else {
      console.error('Kesalahan jaringan:', error.message);
    }
    return Promise.reject(error);
  }
);