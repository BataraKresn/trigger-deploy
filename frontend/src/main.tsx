import './pages/lazy-preload';

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './assets/optimized-images.css';
import axios from 'axios';
import useGlobalState from './store/globalState';

axios.defaults.baseURL = 'http://dev-trigger.mugshot.dev/api/auth';
axios.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    alert('An error occurred while processing your request.');
    return Promise.reject(error);
  }
);

const { darkMode } = useGlobalState.getState();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <div className={darkMode ? 'dark' : ''}>
      <App />
    </div>
  </React.StrictMode>
);
