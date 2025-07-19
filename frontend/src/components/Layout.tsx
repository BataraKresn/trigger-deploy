import React from 'react';
import { Link } from 'react-router-dom';

const Layout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-800 text-white p-4">
        <h2 className="text-xl font-bold mb-6">🚀 Dev Trigger</h2>
        <nav className="space-y-2">
          <Link to="/dashboard" className="block hover:text-yellow-300">Dashboard</Link>
          <Link to="/servers" className="block hover:text-yellow-300">Servers</Link>
          <Link to="/deploy" className="block hover:text-yellow-300">Deploy</Link>
          <Link to="/result" className="block hover:text-yellow-300">Result</Link>
          <Link to="/status" className="block hover:text-yellow-300">Status</Link>
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <main className="p-6 flex-1 bg-gray-100">
          <header className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold">Dashboard Area</h1>
            <button
              className="bg-red-600 text-white px-3 py-1 rounded"
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
        <footer className="bg-gray-200 text-center py-2">
          <p>© Dev Tiger</p>
        </footer>
      </div>
    </div>
  );
};

export default Layout;