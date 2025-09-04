import React from 'react';

interface LayoutShellProps {
  sidebar?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

/**
 * Provides a consistent outer structure: optional sidebar (desktop) + content.
 * Handles horizontal spacing and max width. Top padding handled via global .app-shell class.
 */
export const LayoutShell: React.FC<LayoutShellProps> = ({ sidebar, children, className = '' }) => {
  return (
    <div className={`max-w-7xl mx-auto flex gap-6 ${className}`}> 
      {sidebar && <div className="hidden lg:block w-60 shrink-0">{sidebar}</div>}
      <div className="flex-1 min-w-0">{children}</div>
    </div>
  );
};

export default LayoutShell;
