import axios from 'axios';
import useGlobalState from '@/store/globalState';

// Pastikan baseURL tidak memiliki trailing slash
const baseUrl = import.meta.env.VITE_API_URL.replace(/\/+$/, '');

export const api = axios.create({
  baseURL: baseUrl,
  timeout: 10000,
});

// Tambahkan token Authorization jika tersedia
api.interceptors.request.use((config) => {
  const { token } = useGlobalState.getState();
  if (token) {
    config.headers = {
      ...config.headers,
      Authorization: `Bearer ${token}`,
    };
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