import React from 'react';

export default function App() {
  return (
    <div data-testid="web-shell-root" style={{ fontFamily: 'sans-serif', padding: 40 }}>
      <h1>RealAICoach Web</h1>
      <p>The production web experience is served from the shared cross-platform UI bundle.</p>
      <p>
        Backend: <code>{process.env.REACT_APP_BACKEND_URL}</code>
      </p>
    </div>
  );
}
