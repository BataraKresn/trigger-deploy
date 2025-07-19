import './pages/lazy-preload';

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './assets/optimized-images.css';
import axios from 'axios';

axios.interceptors.response.use(
  (response) => {
    console.log('API Response:', response);
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    alert('An error occurred while processing your request.');
    return Promise.reject(error);
  }
);

console.log('Application initialized');
console.log('Starting React rendering process');

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

console.log('React rendering completed');
