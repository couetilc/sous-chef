import './style.css';
import { useNavigate } from 'react-router';
import { useState } from 'react';

import SousChefLogo from './souschef-logo2.png';

export default function SousChef() {
  const navigate = useNavigate();
  const [sessionActive, setSessionActive] = useState(false);

  const LetUsBeginClicked = () => {
    // Start a cooking session
    setSessionActive(true);
  };
  const ThatsAWrapClicked = () => {
    // End a cooking session
    setSessionActive(false);
  };

  return (
    <div className="centered-div">
      <h1>AI SOUS CHEF</h1>

      {/* centered logo above buttons */}
      <div style={{ textAlign: 'center', marginTop: 8 }}>
        <img src={SousChefLogo} alt="Sous Chef" style={{ width: 160, height: 'auto', display: 'block', margin: '0 auto 12px' }} />
      </div>

      <div style={{ display: 'flex', justifyContent: 'center', gap: 150, marginTop: 12 }}>
        <button onClick={LetUsBeginClicked} style={{ padding: '8px 12px' }}>Let us begin!</button>
        <button onClick={ThatsAWrapClicked} style={{ padding: '8px 12px' }}>That's a wrap!</button>
      </div>

      {/* Cooking session indicator bar (moved below buttons) */}
      <div
        className="cooking-session-bar"
        style={{
          width: '100%',
          maxWidth: 800,
          padding: '8px 12px',
          margin: '12px auto',
          borderRadius: 6,
          backgroundColor: sessionActive ? '#dff7df' : '#f0f0f0',
          color: sessionActive ? '#0a7a2d' : '#444',
          border: sessionActive ? '1px solid #7ad88a' : '1px solid #ddd',
          textAlign: 'center',
          fontWeight: 600,
        }}
      >
        Cooking Session: {sessionActive ? 'Active' : 'Inactive'}
      </div>
    </div>
  )
}
