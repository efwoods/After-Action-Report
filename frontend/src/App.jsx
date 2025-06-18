import { useState } from 'react';
import Login from './components/Login';
import Report from './components/Report';
import CalendarView from './components/CalendarView';
import Dashboard from './components/Dashboard';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');

  return (
    <div className="min-h-screen bg-gray-100">
      {token ? (
        <div className="container mx-auto p-4">
          <h1 className="text-3xl font-bold mb-4">After Action Report</h1>
          <button
            onClick={() => {
              localStorage.removeItem('token');
              setToken('');
            }}
            className="mb-4 bg-red-500 text-white px-4 py-2 rounded"
          >
            Logout
          </button>
          <Report />
          <CalendarView />
          <Dashboard />
        </div>
      ) : (
        <Login setToken={setToken} />
      )}
    </div>
  );
}

export default App;