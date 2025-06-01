import { useState } from 'react';
import axios from 'axios';

function Login({ setToken }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(
        `http://localhost:8000/auth/${isRegister ? 'register' : 'login'}`,
        { email, password }
      );
      if (!isRegister) {
        setToken(response.data.access_token);
        localStorage.setItem('token', response.data.access_token);
      }
      setMessage(isRegister ? 'Registered successfully' : 'Logged in successfully');
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Error occurred');
    }
  };

  const connectService = async (service) => {
    // Redirect to OAuth flow (simplified for demo)
    const clientIds = {
      notion: 'your-notion-client-id',
      github: 'your-github-client-id',
      clockify: 'your-clockify-api-key' // Clockify uses API key, not OAuth
    };
    if (service === 'clockify') {
      const token = prompt('Enter Clockify API Key');
      await axios.post(
        'http://localhost:8000/auth/connect/clockify',
        { token },
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );
      alert('Clockify connected');
    } else {
      window.location.href = service === 'notion'
        ? `https://api.notion.com/v1/oauth/authorize?client_id=${clientIds.notion}&response_type=code&redirect_uri=http://localhost:3000`
        : `https://github.com/login/oauth/authorize?client_id=${clientIds.github}&redirect_uri=http://localhost:3000`;
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded shadow">
      <h2 className="text-2xl font-bold mb-4">{isRegister ? 'Register' : 'Login'}</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          className="w-full p-2 mb-4 border rounded"
          required
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="w-full p-2 mb-4 border rounded"
          required
        />
        <button type="submit" className="w-full bg-blue-500 text-white p-2 rounded">
          {isRegister ? 'Register' : 'Login'}
        </button>
      </form>
      <button
        onClick={() => setIsRegister(!isRegister)}
        className="mt-2 text-blue-500"
      >
        {isRegister ? 'Switch to Login' : 'Switch to Register'}
      </button>
      {message && <p className="mt-2 text-red-500">{message}</p>}
      <div className="mt-4">
        <button
          onClick={() => connectService('notion')}
          className="w-full bg-green-500 text-white p-2 rounded mb-2"
        >
          Connect Notion
        </button>
        <button
          onClick={() => connectService('github')}
          className="w-full bg-gray-800 text-white p-2 rounded mb-2"
        >
          Connect GitHub
        </button>
        <button
          onClick={() => connectService('clockify')}
          className="w-full bg-purple-500 text-white p-2 rounded"
        >
          Connect Clockify
        </button>
      </div>
    </div>
  );
}

export default Login;