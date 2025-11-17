import './style.css';
import {useNavigate} from 'react-router';
import { useApi } from './useApi';
import { useEffect, useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import SousChefLogo from './souschef-logo.png';

function formatTime(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  });
}

export default function Nutritionist() {
  const navigate = useNavigate();
  const { api } = useApi();
  const [currentMessage, setCurrentMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const messagesEndRef = useRef(null);

  // Fetch conversation on mount
  useEffect(() => {
    async function loadConversation() {
      try {
        const response = await api.getConversation();
        if (response.messages) {
          setMessages(response.messages);
        }
      } catch (err) {
        console.error('Failed to load conversation:', err);
      }
    }
    loadConversation();
  }, [api]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function chat() {
    if (!currentMessage?.trim()) return;

    setLoading(true);
    setError(false);

    try {
      const response = await api.nutritionistChat({ message: currentMessage });
      setMessages(response.messages);
      setCurrentMessage('');
    } catch (err) {
      console.error('Chat error:', err);
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  async function handleClear() {
    if (!confirm('Clear conversation history?')) return;

    try {
      await api.clearConversation();
      setMessages([]);
      setError(false);
    } catch (err) {
      console.error('Clear error:', err);
      setError(true);
    }
  }

  return (
    <div className="nutritionist-page">
      <h1>NUTRITIONIST</h1>

      <div className="chat-messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.role === 'assistant' ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {msg.content}
                </ReactMarkdown>
              ) : (
                msg.content
              )}
            </div>
            <div className="message-time">{formatTime(msg.created_at)}</div>
          </div>
        ))}
        {loading && (
          <div className="loading-indicator">Thinking...</div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input">
        <textarea
          value={currentMessage}
          onChange={e => setCurrentMessage(e.target.value)}
          disabled={loading}
          placeholder="Ask me about nutrition..."
        />
        <div className="button-row">
          <button
            type="button"
            className="button-blue"
            onClick={handleClear}
            disabled={loading}
          >
            Clear
          </button>
          <div className="chat-button-group">
            {error && <span className="error-indicator">✕</span>}
            <button
              type="button"
              className="button"
              onClick={chat}
              disabled={loading || !currentMessage?.trim()}
            >
              {loading ? 'Loading...' : 'Chat'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
