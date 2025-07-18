import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import axios from 'axios';

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    alert('An error occurred while processing your request.');
    return Promise.reject(error);
  }
);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
