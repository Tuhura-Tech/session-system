import React from "react";

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
  actions?: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children, title, actions }) => {
  return (
    <div className="min-h-screen bg-gray-100">
      {title && (
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex justify-between items-center">
              <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
              {actions && <div>{actions}</div>}
            </div>
          </div>
        </header>
      )}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
};

export default Layout;
