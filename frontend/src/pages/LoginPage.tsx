import React, { useState } from 'react';
import axios from 'axios';
import { AxiosError } from 'axios';
import useGlobalState from '../store/globalState';

function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { setToken } = useGlobalState();

  const handleLogin = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/login', { username, password });
      const data = response.data as { token: string };
      if (data.token) {
        localStorage.setItem('authToken', data.token); // Store token
        window.location.href = '/dashboard'; // Redirect to dashboard
      } else {
        setError('Login failed: No token received');
      }
    } catch (err) {
      const axiosError = err as AxiosError;
      if (axiosError.response) {
        const errorData = axiosError.response.data as { detail?: string };
        setError(errorData.detail || 'Invalid username or password');
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-r from-blue-500 to-purple-600">
      <div className="w-full max-w-md p-6 bg-white rounded-lg shadow-lg">
        <h2 className="text-3xl font-bold text-center text-gray-800 mb-6">🚀 Login to Trigger Deploy</h2>
        {error && <p className="text-red-500 text-center mb-4" role="alert">{error}</p>}
        {loading && <p className="text-blue-500 text-center mb-4">Loading...</p>}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleLogin();
          }}
        >
          <div className="mb-4">
            <label className="block text-gray-700 font-medium" htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter your username"
              autoComplete="username"
            />
          </div>
          <div className="mb-4">
            <label className="block text-gray-700 font-medium" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter your password"
              autoComplete="current-password"
            />
          </div>
          <button
            type="submit"
            className="w-full bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Login
          </button>
        </form>
      </div>
    </div>
  );
}

export default LoginPage;
