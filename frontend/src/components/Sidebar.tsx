import React, { useState } from 'react';
import { Home, Server, Activity, Heart, FileText, Settings, Moon, Sun } from 'lucide-react';

const Sidebar = () => {
  const [darkMode, setDarkMode] = useState(false);

  const menuItems = [
    { name: 'Dashboard', icon: <Home />, path: '/dashboard' },
    { name: 'Server List', icon: <Server />, path: '/servers' },
    { name: 'Deploy', icon: <Activity />, path: '/deploy' },
    { name: 'Health Check', icon: <Heart />, path: '/health' },
    { name: 'Logs', icon: <FileText />, path: '/logs' },
    { name: 'Settings', icon: <Settings />, path: '/settings' },
  ];

  return (
    <div className={`w-64 h-screen flex flex-col ${darkMode ? 'bg-gray-900 text-white' : 'bg-gray-100 text-black'}`}>
      <div className="p-4 text-lg font-bold flex justify-between items-center">
        <span>Trigger Deploy</span>
        <button
          onClick={() => setDarkMode(!darkMode)}
          className="p-2 rounded-full hover:bg-gray-300 transition-all"
        >
          {darkMode ? <Sun /> : <Moon />}
        </button>
      </div>
      <nav className="flex-1">
        {menuItems.map((item) => (
          <a
            key={item.name}
            href={item.path}
            className="flex items-center gap-4 py-2 px-4 hover:bg-gray-700 transition-all"
          >
            {item.icon}
            <span>{item.name}</span>
          </a>
        ))}
      </nav>
    </div>
  );
};

export default Sidebar;