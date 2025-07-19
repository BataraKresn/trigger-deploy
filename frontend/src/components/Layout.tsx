import React from 'react';

const Layout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div>
      {children}
      <footer>
        <p>© Dev Tiger</p>
      </footer>
    </div>
  );
};

export default Layout;
