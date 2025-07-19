import React from 'react';
import { Link } from 'react-router-dom';

const Layout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="flex min-h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-gradient-to-b from-blue-600 to-blue-800 text-white p-6 shadow-lg">
        <h2 className="text-2xl font-bold mb-6 text-center">🚀 Dev Trigger</h2>
        <nav className="space-y-4">
          <Link
            to="/dashboard"
            className="block py-2 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Dashboard
          </Link>
          <Link
            to="/servers"
            className="block py-2 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Servers
          </Link>
          <Link
            to="/deploy"
            className="block py-2 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Deploy
          </Link>
          <Link
            to="/result"
            className="block py-2 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Result
          </Link>
          <Link
            to="/status"
            className="block py-2 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Status
          </Link>
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <main className="p-6 flex-1">
          <header className="flex justify-between items-center mb-6 bg-white shadow-md p-4 rounded-lg">
            <h1 className="text-2xl font-bold text-gray-800">Dashboard Area</h1>
            <button
              className="bg-red-500 text-white py-2 px-4 rounded-lg hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500"
              onClick={() => {
                localStorage.clear();
                window.location.href = '/login';
              }}
            >
              Logout
            </button>
          </header>

          {children}
        </main>

        {/* Footer */}
        <footer className="bg-gray-200 text-center py-4">
          <p className="text-gray-600">© 2025 Dev Trigger</p>
        </footer>
      </div>
    </div>
  );
};

export default Layout;