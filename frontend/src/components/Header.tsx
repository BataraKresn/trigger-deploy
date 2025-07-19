import React from 'react';

const Header = ({ onToggleDarkMode }: { onToggleDarkMode: () => void }) => {
  return (
    <header className="bg-gray-900 text-white p-4 flex justify-between items-center">
      <div className="text-lg font-bold">Trigger Deploy</div>
      <div className="flex items-center gap-4">
        <button
          onClick={onToggleDarkMode}
          className="py-2 px-4 bg-gray-700 hover:bg-gray-600 rounded"
        >
          Toggle Dark Mode
        </button>
        <div className="text-sm">Logged in as Admin</div>
      </div>
    </header>
  );
};

export default Header;