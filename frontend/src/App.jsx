import React from 'react';
import LogInteractionScreen from './components/LogInteractionScreen';

function App() {
  return (
    <div className="App">
      <nav style={{ 
        padding: '20px 40px', 
        borderBottom: '1px solid var(--border)', 
        display: 'flex', 
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'rgba(15, 23, 42, 0.8)',
        backdropFilter: 'blur(8px)',
        position: 'sticky',
        top: 0,
        zIndex: 100
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ 
            width: '32px', 
            height: '32px', 
            background: 'var(--primary)', 
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 'bold',
            color: 'white'
          }}>A</div>
          <span style={{ fontWeight: 600, fontSize: '1.2rem', letterSpacing: '-0.5px' }}>AiVoa CRM</span>
        </div>
        <div style={{ display: 'flex', gap: '24px', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          <span style={{ cursor: 'pointer', color: 'var(--text)' }}>HCP Module</span>
          <span style={{ cursor: 'pointer' }}>Analytics</span>
          <span style={{ cursor: 'pointer' }}>Campaigns</span>
          <span style={{ cursor: 'pointer' }}>Settings</span>
        </div>
      </nav>
      <main>
        <LogInteractionScreen />
      </main>
      <footer style={{ 
        textAlign: 'center', 
        padding: '40px', 
        color: 'var(--text-muted)', 
        fontSize: '0.8rem',
        borderTop: '1px solid var(--border)',
        marginTop: '60px'
      }}>
        &copy; 2026 AiVoa Life Sciences. Powered by LangGraph & Groq.
      </footer>
    </div>
  );
}

export default App;
