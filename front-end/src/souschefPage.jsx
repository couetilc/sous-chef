import './style.css';
import { useNavigate, useParams } from 'react-router';
import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

import SousChefLogo from './souschef-logo2.png';
import { useApi } from './useApi';

function formatTime(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

export default function SousChef() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { api } = useApi();

  const [sessionActive, setSessionActive] = useState(false);

  const [currentMessage, setCurrentMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const messagesEndRef = useRef(null);

  console.log('SousChefPage recipe id:', id);

  // Placeholder recipe for User Story 7 (will later be replaced with real DB recipe)
  const placeholderRecipe = {
    title: 'Garlic Butter Chicken with Veggies',
    image_url: null,
    servings: 2,
    prep_time_min: 10,
    cook_time_min: 20,
    ingredients: [
      '2 chicken breasts',
      '2 tbsp butter',
      '3 cloves garlic, minced',
      '1 cup broccoli florets',
      '1 carrot, sliced',
      'Salt & pepper to taste',
    ],
    instructions: [
      'Season chicken with salt and pepper.',
      'Pan-sear chicken in butter until golden and cooked through.',
      'Add garlic, then the vegetables, and sauté until tender-crisp.',
      'Taste and adjust seasoning, then serve warm.',
    ],
  };

  // Fetch SousChef conversation on mount
  useEffect(() => {
    async function loadConversation() {
      try {
        const response = await api.getSousChefConversation();
        if (response.messages) {
          setMessages(response.messages);
        }
      } catch (err) {
        console.error('Failed to load SousChef conversation:', err);
      }
    }
    loadConversation();
  }, [api]);

  // Auto-scroll chat to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const LetUsBeginClicked = () => {
    // Start a cooking session (for now just UI; later hook to backend)
    setSessionActive(true);
  };

  const ThatsAWrapClicked = () => {
    // End a cooking session
    setSessionActive(false);
  };

  async function chat() {
    if (!currentMessage?.trim()) return;

    setLoading(true);
    setError(false);

    try {
      const response = await api.sousChefChat({ message: currentMessage });
      setMessages(response.messages);
      setCurrentMessage('');
    } catch (err) {
      console.error('SousChef chat error:', err);
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  async function handleClear() {
    if (!confirm('Clear SousChef conversation history?')) return;

    try {
      await api.clearSousChefConversation();
      setMessages([]);
      setError(false);
    } catch (err) {
      console.error('SousChef clear error:', err);
      setError(true);
    }
  }

  return (
    <div
      className="souschef-page-wrapper"
      style={{
        width: '100%',
        display: 'flex',
        justifyContent: 'center',
        padding: '24px 24px 32px',
        boxSizing: 'border-box',
      }}
    >
      <div
        className="centered-div souschef-page"
        style={{
          width: '100%',
          maxWidth: 1100,
          margin: '0 auto',
          boxSizing: 'border-box',
        }}
      >
        <header style={{ textAlign: 'center', marginBottom: 12 }}>
          <h1 style={{ margin: 0, letterSpacing: 1 }}>AI SOUS CHEF</h1>

          <div style={{ marginTop: 10 }}>
            {id && (
              <div style={{ fontSize: 13, color: '#777', marginTop: 2 }}>
                Cooking recipe ID: {id}
              </div>
            )}
          </div>

          {/* Cooking session indicator bar */}
          <div
            className="cooking-session-bar"
            style={{
              width: '100%',
              maxWidth: 640,
              padding: '8px 12px',
              margin: '16px auto 0',
              borderRadius: 999,
              backgroundColor: sessionActive ? '#e5f8ea' : '#f3f3f3',
              color: sessionActive ? '#137a3b' : '#555',
              border: sessionActive ? '1px solid #8bd79d' : '1px solid #ddd',
              textAlign: 'center',
              fontWeight: 600,
              fontSize: 14,
            }}
          >
            Cooking Session: {sessionActive ? 'Active' : 'Inactive'}
          </div>
        </header>

        {/* Main layout: recipe panel + chat panel */}
        <div
          className="souschef-layout"
          style={{
            display: 'flex',
            gap: 24,
            alignItems: 'stretch',
            marginTop: 20,
          }}
        >
          {/* LEFT: Recipe display */}
          <section
            className="souschef-recipe-panel"
            style={{
              flex: 1,
              border: '1px solid #e3e3e3',
              borderRadius: 10,
              padding: 16,
              backgroundColor: '#fafafa',
              minWidth: 0,
            }}
          >
            <h2 style={{ marginTop: 0, marginBottom: 6, fontSize: 20 }}>
              Current Recipe
            </h2>
            <div style={{ fontSize: 13, color: '#777', marginBottom: 10 }}>
              (Prototype) This is a placeholder recipe. Later this will load
              recipe #{id} from the database.
            </div>

            <div className="recipe-card">
              {placeholderRecipe.image_url && (
                <img
                  src={placeholderRecipe.image_url}
                  alt={placeholderRecipe.title}
                  className="recipe-image"
                  style={{
                    width: '100%',
                    maxHeight: 220,
                    objectFit: 'cover',
                    borderRadius: 6,
                    marginBottom: 12,
                  }}
                />
              )}
              <h3 style={{ marginBottom: 4 }}>{placeholderRecipe.title}</h3>
              <div
                className="recipe-meta"
                style={{
                  display: 'flex',
                  gap: 12,
                  fontSize: 14,
                  color: '#555',
                  marginBottom: 10,
                  flexWrap: 'wrap',
                }}
              >
                <span>Servings: {placeholderRecipe.servings}</span>
                <span>
                  Time:{' '}
                  {placeholderRecipe.prep_time_min +
                    placeholderRecipe.cook_time_min}{' '}
                  min
                </span>
              </div>

              <div className="recipe-section" style={{ marginBottom: 10 }}>
                <h4 style={{ marginBottom: 4 }}>Ingredients</h4>
                <ul style={{ paddingLeft: 18, margin: 0 }}>
                  {placeholderRecipe.ingredients.map((ing, idx) => (
                    <li key={idx} style={{ fontSize: 14, marginBottom: 2 }}>
                      {ing}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="recipe-section">
                <h4 style={{ marginBottom: 4 }}>Instructions</h4>
                <ol style={{ paddingLeft: 18, margin: 0 }}>
                  {placeholderRecipe.instructions.map((step, idx) => (
                    <li key={idx} style={{ fontSize: 14, marginBottom: 4 }}>
                      {step}
                    </li>
                  ))}
                </ol>
              </div>
            </div>
          </section>

          {/* RIGHT: Chat panel */}
          <section
            className="souschef-chat-panel"
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              border: '1px solid #e3e3e3',
              borderRadius: 10,
              padding: 16,
              backgroundColor: '#ffffff',
              minWidth: 0,
              maxHeight: 700,
            }}
          >
            <h2 style={{ marginTop: 0, marginBottom: 6, fontSize: 20 }}>
              Ask SousChef
            </h2>
            <div style={{ fontSize: 13, color: '#666', marginBottom: 8 }}>
              Prompt suggestions:
              <ul style={{ margin: '4px 0 0 16px', padding: 0 }}>
                <li>“Can I substitute broccoli for green beans?”</li>
                <li>“How do I know when the chicken is cooked?”</li>
                <li>“Let&apos;s move on to the next step.”</li>
              </ul>
            </div>

            <div
              className="chat-messages"
              style={{
                flexShrink: 0,
                height: 260, // bounds the chat area
                overflowY: 'auto',
                border: '1px solid #eee',
                borderRadius: 6,
                padding: 8,
                marginBottom: 8,
                backgroundColor: '#fafafa',
              }}
            >
              {messages.map((msg) => {
                const isAssistant = msg.role === 'assistant';
                return (
                  <div
                    key={msg.id}
                    className={`message ${msg.role}`}
                    style={{
                      marginBottom: 8,
                      padding: 6,
                      borderRadius: 6,
                      backgroundColor: isAssistant ? '#ffffff' : '#a83232',
                      border: isAssistant
                        ? '1px solid #e5e5e5'
                        : '1px solid #a83232',
                      color: isAssistant ? '#000' : '#ffffff',
                    }}
                  >
                    <div
                      className="message-content"
                      style={{ fontSize: 14, marginBottom: 2 }}
                    >
                      {isAssistant ? (
                        <ReactMarkdown
                          components={{
                            p: ({ node, ...props }) => (
                              <p style={{ margin: 0 }} {...props} />
                            ),
                          }}
                        >
                          {msg.content}
                        </ReactMarkdown>
                      ) : (
                        msg.content
                      )}
                    </div>
                    <div
                      className="message-time"
                      style={{
                        fontSize: 11,
                        color: isAssistant ? '#999' : '#ffd9d9',
                        textAlign: 'right',
                      }}
                    >
                      {formatTime(msg.created_at)}
                    </div>
                  </div>
                );
              })}
              {loading && (
                <div
                  className="loading-indicator"
                  style={{ fontSize: 13, color: '#777' }}
                >
                  Thinking...
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="chat-input" style={{ marginTop: 'auto' }}>
              <textarea
                value={currentMessage}
                onChange={(e) => setCurrentMessage(e.target.value)}
                disabled={loading}
                placeholder="Ask SousChef to clarify an instruction, give cooking tips, or move on to the next step..."
                style={{
                  width: '100%',
                  minHeight: 80,
                  maxHeight: 140,
                  resize: 'vertical',
                  marginBottom: 8,
                  padding: 8,
                  borderRadius: 6,
                  border: '1px solid #ddd',
                  fontSize: 14,
                  boxSizing: 'border-box',
                }}
              />
              <div
                className="button-row"
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <button
                  type="button"
                  className="button-blue"
                  onClick={handleClear}
                  disabled={loading}
                  style={{
                    padding: '6px 14px',
                    borderRadius: 999,
                    border: '1px solid #ccc',
                    backgroundColor: '#f1f1f1',
                    cursor: 'pointer',
                    fontSize: 14,
                  }}
                >
                  Clear
                </button>
                <div
                  className="chat-button-group"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  {error && (
                    <span
                      className="error-indicator"
                      style={{ color: '#a83232', fontSize: 16 }}
                    >
                      ✕
                    </span>
                  )}
                  <button
                    type="button"
                    className="button"
                    onClick={chat}
                    disabled={loading || !currentMessage?.trim()}
                    style={{
                      padding: '6px 18px',
                      borderRadius: 999,
                      border: '1px solid #a83232',
                      backgroundColor: loading ? '#f3a3a3' : '#a83232',
                      color: '#fff',
                      cursor:
                        loading || !currentMessage?.trim()
                          ? 'not-allowed'
                          : 'pointer',
                      fontSize: 14,
                    }}
                  >
                    {loading ? 'Loading...' : 'Chat'}
                  </button>
                </div>
              </div>
            </div>
          </section>
        </div>

        {/* Footer buttons: bottom left & right */}
        <footer
          style={{
            marginTop: 18,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <button
            onClick={LetUsBeginClicked}
            style={{
              padding: '8px 16px',
              borderRadius: 999,
              border: '1px solid #ddd',
              backgroundColor: '#f7f7f7',
              color: '#000',
              cursor: 'pointer',
            }}
          >
            Let us begin!
          </button>

          <button
            onClick={ThatsAWrapClicked}
            style={{
              padding: '8px 16px',
              borderRadius: 999,
              border: '1px solid #a83232',
              backgroundColor: '#a83232',
              color: '#fff',
              cursor: 'pointer',
            }}
          >
            That&apos;s a wrap!
          </button>
        </footer>
      </div>
    </div>
  );
}
