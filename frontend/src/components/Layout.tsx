import React from 'react';
import { motion } from 'framer-motion';
import Sidebar from './Sidebar';
import Header from './Header';
import useGlobalState from '@/store/globalState';

interface LayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
}

const Layout: React.FC<LayoutProps> = ({ children, title, subtitle }) => {
  const { sidebarCollapsed, darkMode } = useGlobalState();

  return (
    <div className={`min-h-screen ${darkMode ? 'dark bg-gray-950' : 'bg-gray-50'}`}>
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main Content Area */}
      <div 
        className="transition-all duration-300 ease-in-out"
        style={{
          marginLeft: sidebarCollapsed ? '80px' : '280px'
        }}
      >
        {/* Header */}
        <Header title={title} subtitle={subtitle} />
        
        {/* Page Content */}
        <motion.main
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="p-6"
        >
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </motion.main>
        
        {/* Footer */}
        <footer className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-6 py-4">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
              <div className="flex items-center gap-4">
                <span>© 2025 Trigger Deploy</span>
                <span>•</span>
                <span>Professional DevOps Platform</span>
              </div>
              <div className="flex items-center gap-4">
                <span>v1.0.0</span>
                <span>•</span>
                <span>Status: All Systems Operational</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default Layout;