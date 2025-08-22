// index.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';

import App from './App';
import { ErrorBoundary } from './components/ErrorBoundary';
import './index.css'; // Ensure Tailwind CSS is imported

// Ensure the root element exists
const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Root element not found. Make sure you have a div with id="root" in your HTML.');
}

const root = ReactDOM.createRoot(rootElement);

root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);

// Optional: Add global error handler for unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  // Optionally show user-friendly error notification
});