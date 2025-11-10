import './style.css';
import {useNavigate} from 'react-router';
import { useApi } from './useApi';
import { useEffect, useState } from 'react';

import SousChefLogo from './souschef-logo.png';

export default function Nutritionist() {
  const navigate = useNavigate();
  const { api } = useApi();
  const [message, setMessage] = useState()
  const [loading, setLoading] = useState(false)

  async function chat() {
    setLoading(true)
    try {
      const response = await api.nutritionistChat({ message, })
      document.querySelector('#chat-response').innerText = response.message
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="nutritionist-page">
      <h1>NUTRITIONIST</h1>
      <div className="user-message">
        <textarea value={message} onChange={e => setMessage(e.target.value)}>
        </textarea>
        <button type="button" className="button" onClick={() => chat()} disabled={loading}>
          { loading ? 'Loading...' : 'Chat' }
        </button>
      </div>
      <p id="chat-response">
      </p>
    </div>
  )
}
