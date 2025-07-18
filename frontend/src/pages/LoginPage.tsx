import React, { useState } from 'react';
import axios from 'axios';
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
      setToken(response.data.token);
      window.location.href = '/dashboard';
    } catch (err) {
      setError('Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Login</h1>
      {error && <p className="text-red-500" role="alert">{error}</p>}
      {loading && <p className="text-blue-500">Loading...</p>}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleLogin();
        }}
        aria-label="Login Form"
      >
        <div className="mb-4">
          <label className="block text-gray-700" htmlFor="username">Username</label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="input"
            aria-required="true"
          />
        </div>
        <div className="mb-4">
          <label className="block text-gray-700" htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input"
            aria-required="true"
          />
        </div>
        <button type="submit" className="btn" aria-label="Login Button">
          Login
        </button>
      </form>
    </div>
  );
}

export default LoginPage;
