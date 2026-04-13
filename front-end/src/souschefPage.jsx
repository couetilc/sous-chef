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

// Normalize a field that may be an array or a pipe-separated string
function toList(field) {
  if (Array.isArray(field)) return field;
  if (typeof field === 'string') {
    return field
      .split('|')
      .map((s) => s.trim())
      .filter(Boolean);
  }
  return [];
}

// Convert decimal values close to n/3 into "n/3" (e.g., 0.6666 → 2/3, 1.6666 → 5/3)
function toThirdsFraction(value) {
  const val = parseFloat(value)
  if (!Number.isFinite(val)) return null

  // Leave clean integers alone (e.g., 1.0, 2.0)
  const roundedInt = Math.round(val)
  if (Math.abs(val - roundedInt) < 0.01) {
    return null
  }

  // Approximate as n/3
  const n = Math.round(val * 3)
  const approx = n / 3

  // Only accept if:
  // - it's actually a non-integer multiple of 1/3
  // - it's close enough to the original value
  if (n > 0 && n % 3 !== 0 && Math.abs(approx - val) < 0.02) {
    return `${n}/3`
  }

  return null
}

// Replace any decimal in the string that's close to n/3 with "n/3"
function formatIngredientAmountInString(text) {
  if (typeof text !== 'string') return text

  const numberRegex = /-?\d*\.?\d+/g

  return text.replace(numberRegex, (match) => {
    const fraction = toThirdsFraction(match)
    return fraction || match
  })
}


export default function SousChef() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { api } = useApi();

  const [cookingSession, setCookingSession] = useState(null);
  const [sessionHistory, setSessionHistory] = useState([]);

  const [currentMessage, setCurrentMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const messagesEndRef = useRef(null);

  const [recipe, setRecipe] = useState(null);
  const [recipeError, setRecipeError] = useState(null);

  // Voice communication state
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);
  const [autoPlayResponses, setAutoPlayResponses] = useState(true);
  const [availableVoices, setAvailableVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState(null);
  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);
  const autoSendAfterSpeechRef = useRef(true);
  const lastSpokenMessageIdRef = useRef(null);

  console.log('SousChefPage recipe id:', id);

  // Initialize speech recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      console.warn('Speech recognition not supported in this browser');
      setSpeechSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      console.log('Speech recognition started');
      setIsListening(true);
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      console.log('Speech recognized:', transcript);
      setCurrentMessage(transcript);
      setIsListening(false);
      
      // Auto-send the message after voice input
      if (autoSendAfterSpeechRef.current && transcript.trim()) {
        // Need to wait for state update, then trigger chat
        setTimeout(() => {
          handleVoiceAutoSend(transcript);
        }, 150);
      }
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
      if (event.error === 'not-allowed') {
        alert('Microphone access denied. Please enable microphone permissions.');
      }
    };

    recognition.onend = () => {
      console.log('Speech recognition ended');
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, []);

  // Load available voices and select a good default
  useEffect(() => {
    const loadVoices = () => {
      const voices = synthRef.current.getVoices();
      setAvailableVoices(voices);
      
      if (voices.length > 0 && !selectedVoice) {
        // Try to find a good male English voice for a chef
        // Prefer voices with these characteristics for a chef persona
        const preferredVoices = [
          voices.find(v => v.name.includes('Daniel') && v.lang.startsWith('en')),
          voices.find(v => v.name.includes('Fred') && v.lang.startsWith('en')),
          voices.find(v => v.name.includes('Thomas') && v.lang.startsWith('en')),
          voices.find(v => v.name.includes('Male') && v.lang.startsWith('en')),
          voices.find(v => v.name.includes('Gordon') && v.lang.startsWith('en')),
          voices.find(v => v.lang.startsWith('en-GB')), // British accent works well for cooking
          voices.find(v => v.lang.startsWith('en-US')),
          voices.find(v => v.lang.startsWith('en')),
        ].filter(Boolean);
        
        const defaultVoice = preferredVoices[0] || voices[0];
        setSelectedVoice(defaultVoice);
        console.log('Selected voice:', defaultVoice?.name);
      }
    };

    // Load voices immediately
    loadVoices();
    
    // Some browsers load voices asynchronously
    if (synthRef.current.onvoiceschanged !== undefined) {
      synthRef.current.onvoiceschanged = loadVoices;
    }
    
    return () => {
      if (synthRef.current) {
        synthRef.current.onvoiceschanged = null;
      }
    };
  }, [selectedVoice]);

  // Cleanup speech synthesis on unmount
  useEffect(() => {
    return () => {
      if (synthRef.current) {
        synthRef.current.cancel();
      }
    };
  }, []);

  // Clear messages, conversation, and cooking session when navigating to a different recipe
  useEffect(() => {
    setMessages([]);
    setCookingSession(null); // Reset cooking session state
    // Stop any ongoing speech
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
    // Clear the backend conversation as well
    const clearConversation = async () => {
      try {
        await api.clearSousChefConversation();
      } catch (err) {
        console.error('Failed to clear SousChef conversation on navigation:', err);
      }
    };
    clearConversation();
  }, [id, api]);

  const placeholderRecipe = {
    title: 'Garlic Butter Chicken with Veggies',
    image_url: null,
    servings: 2,
    prep_time_min: 10,
    cook_time_min: 20,
    ingredients:
      '2 chicken breasts | 2 tbsp butter | 3 cloves garlic, minced | 1 cup broccoli florets | 1 carrot, sliced | Salt & pepper to taste',
    instructions:
      'Season chicken with salt and pepper. | Pan-sear chicken in butter until golden and cooked through. | Add garlic, then the vegetables, and sauté until tender-crisp. | Taste and adjust seasoning, then serve warm.',
  };

  // Load recipe details from backend
  useEffect(() => {
    if (!id) return;

    let cancelled = false;

    async function loadRecipe() {
      try {
        const data = await api.getRecipeDetail({ id });
        if (!cancelled) {
          setRecipe(data);
          setRecipeError(null);
        }
      } catch (err) {
        console.error('Failed to load recipe for SousChef:', err);
        if (!cancelled) {
          setRecipeError('Unable to load recipe details.');
        }
      }
    }

    loadRecipe();
    return () => {
      cancelled = true;
    };
  }, [api, id]);

  // Load or start cooking session for the current recipe
  useEffect(() => {
    if (!id) return;

    let cancelled = false;

    async function loadOrStartSession() {
      console.log('loadOrStartSession called for recipe ID:', id);
      
      try {
        // First try to get existing active session
        const existingSession = await api.getCookingSession({ recipe_id: Number(id) });
        console.log('getCookingSession response:', existingSession);
        
        if (!cancelled && existingSession && existingSession.id) {
          // Resume existing session
          console.log('Resuming existing cooking session:', existingSession);
          setCookingSession(existingSession);
          return; // Exit early
        }
      } catch (err) {
        // If we get a 404, there's no active session - that's expected
        console.log('getCookingSession error (expected 404):', err.status, err);
      }

      // If we get here, either there was no session or we got a 404
      // Start a new session
      if (!cancelled) {
        console.log('Starting new cooking session for recipe:', id);
        try {
          const newSession = await api.startCookingSession({
            recipe_id: Number(id),
          });
          console.log('startCookingSession response:', newSession);
          if (!cancelled && newSession) {
            setCookingSession(newSession);
            console.log('Session state set to:', newSession);
          }
        } catch (startErr) {
          console.error('Failed to start new cooking session:', startErr);
        }
      }
    }

    loadOrStartSession();
    return () => {
      cancelled = true;
    };
  }, [api, id]);

  // Load SousChef conversation (clear when recipe changes)
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
  }, [api, id]);

  // Load cooking session history
  useEffect(() => {
    async function loadHistory() {
      try {
        const history = await api.getCookingSessionHistory();
        setSessionHistory(history || []);
      } catch (err) {
        console.error('Failed to load cooking session history:', err);
      }
    }
    loadHistory();
  }, [api]);

  // Auto scroll chat and speak assistant responses
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    
    // Speak the latest assistant message if autoplay is enabled
    if (autoPlayResponses && messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.role === 'assistant' && lastMessage.id !== lastSpokenMessageIdRef.current) {
        // Only speak if this is a new message we haven't spoken yet
        lastSpokenMessageIdRef.current = lastMessage.id;
        speakText(lastMessage.content);
      }
    }
  }, [messages, autoPlayResponses]);

  // Voice input functions
  function startListening() {
    if (!recognitionRef.current || isListening) return;
    
    try {
      // Stop any ongoing speech
      if (synthRef.current) {
        synthRef.current.cancel();
        setIsSpeaking(false);
      }
      
      recognitionRef.current.start();
    } catch (err) {
      console.error('Failed to start speech recognition:', err);
    }
  }

  function stopListening() {
    if (!recognitionRef.current || !isListening) return;
    
    try {
      recognitionRef.current.stop();
    } catch (err) {
      console.error('Failed to stop speech recognition:', err);
    }
  }

  // Text-to-speech function
  function speakText(text) {
    if (!synthRef.current) return;
    
    // Cancel any ongoing speech
    synthRef.current.cancel();
    
    // Remove markdown formatting for better speech
    const cleanText = text
      .replace(/[*_~`]/g, '') // Remove markdown formatting
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Convert links to just text
      .replace(/#+\s/g, '') // Remove heading markers
      .replace(/\n+/g, '. '); // Convert newlines to pauses
    
    const utterance = new SpeechSynthesisUtterance(cleanText);
    
    // Use selected voice if available
    if (selectedVoice) {
      utterance.voice = selectedVoice;
      utterance.lang = selectedVoice.lang;
    } else {
      utterance.lang = 'en-US';
    }
    
    utterance.rate = 0.95; // Slightly slower for clarity
    utterance.pitch = 1.0;
    
    utterance.onstart = () => {
      setIsSpeaking(true);
    };
    
    utterance.onend = () => {
      setIsSpeaking(false);
    };
    
    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event);
      setIsSpeaking(false);
    };
    
    synthRef.current.speak(utterance);
  }

  function stopSpeaking() {
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  }

  // Handle auto-send after voice input
  async function handleVoiceAutoSend(transcript) {
    if (!transcript?.trim()) return;

    setLoading(true);
    setError(false);
    
    // Stop any ongoing speech
    stopSpeaking();

    try {
      const payload = {
        message: transcript,
      };
      if (id) {
        payload.recipe_id = Number(id);
      }

      const response = await api.sousChefChat(payload);
      setMessages(response.messages);

      // Update cooking session if included in response
      if (response.cooking_session) {
        setCookingSession(response.cooking_session);
      }

      // Check if backend signaled to end the session
      if (response.should_end_session) {
        // Clear the cooking session state
        setCookingSession(null);
        
        // Reload session history to show the newly completed session
        try {
          const history = await api.getCookingSessionHistory();
          setSessionHistory(history || []);
        } catch (err) {
          console.error('Failed to reload session history:', err);
        }
      }

      setCurrentMessage('');
    } catch (err) {
      console.error('SousChef chat error:', err);
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  async function chat() {
    if (!currentMessage?.trim()) return;

    setLoading(true);
    setError(false);
    
    // Stop any ongoing speech when user sends a message
    stopSpeaking();

    try {
      const payload = {
        message: currentMessage,
      };
      if (id) {
        payload.recipe_id = Number(id);
      }

      const response = await api.sousChefChat(payload);
      setMessages(response.messages);

      // Update cooking session if included in response
      if (response.cooking_session) {
        setCookingSession(response.cooking_session);
      }

      // Check if backend signaled to end the session
      if (response.should_end_session) {
        // Clear the cooking session state
        setCookingSession(null);
        
        // Reload session history to show the newly completed session
        try {
          const history = await api.getCookingSessionHistory();
          setSessionHistory(history || []);
        } catch (err) {
          console.error('Failed to reload session history:', err);
        }
      }

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

  async function handleEndSession() {
    if (!id || !cookingSession) return;
    
    if (!confirm('End this cooking session? This will be saved to your session history.')) return;

    // Stop any ongoing speech
    stopSpeaking();

    try {
      await api.endCookingSession({ recipe_id: Number(id) });
      
      // Reload the conversation to show the completion message
      const response = await api.getSousChefConversation();
      if (response.messages) {
        setMessages(response.messages);
      }
      
      // Reload session history
      const history = await api.getCookingSessionHistory();
      setSessionHistory(history || []);
      
      // Clear the cooking session
      setCookingSession(null);
      setError(false);
    } catch (err) {
      console.error('Failed to end cooking session:', err);
      setError(true);
    }
  }

  // Active recipe (DB if available, else placeholder)
  const activeRecipe = recipe || placeholderRecipe;
  const ingredientList = toList(activeRecipe.ingredients).map(formatIngredientAmountInString);
  const instructionList = toList(activeRecipe.instructions);

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
          <h1 style={{ margin: 0, letterSpacing: 1 }}>SOUS CHEF</h1>

          <div style={{ marginTop: 10 }}>
            {id && (
              <div style={{ fontSize: 13, color: '#777', marginTop: 2 }}>
              </div>
            )}
            {cookingSession && (
              <div
                style={{
                  display: 'inline-block',
                  marginTop: 8,
                  padding: '6px 12px',
                  borderRadius: 999,
                  backgroundColor: '#aa0808ff',
                  color: '#fff',
                  fontSize: 13,
                  fontWeight: 600,
                }}
              >
                Cooking Session Active
              </div>
            )}
          </div>
        </header>

        <div
          className="souschef-layout"
          style={{
            display: 'flex',
            gap: 24,
            alignItems: 'stretch',
            marginTop: 20,
          }}
        >
          {/* LEFT: Recipe panel */}
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
              {recipeError
                ? recipeError
                : recipe
                ? `Loaded from your recipe library.`
                : `(Prototype) This is a placeholder recipe. Later this will load recipe #${id} from the database.`}
            </div>

            <div className="recipe-card">
              {activeRecipe.image_url && (
                <img
                  src={activeRecipe.image_url}
                  alt={activeRecipe.title}
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
              <h3 style={{ marginBottom: 4 }}>{activeRecipe.title}</h3>
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
                {activeRecipe.servings != null && (
                  <span>Servings: {activeRecipe.servings}</span>
                )}
                {(activeRecipe.prep_time_min != null ||
                  activeRecipe.cook_time_min != null) && (
                  <span>
                    Time: {' '}
                    {(activeRecipe.prep_time_min || 0) +
                      (activeRecipe.cook_time_min || 0)}{' '}
                    min
                  </span>
                )}
              </div>

              <div className="recipe-section" style={{ marginBottom: 10 }}>
                <h4 style={{ marginBottom: 4 }}>Ingredients</h4>
                <ul style={{ paddingLeft: 18, margin: 0 }}>
                  {ingredientList.map((ing, idx) => (
                    <li key={idx} style={{ fontSize: 14, marginBottom: 2 }}>
                      {ing}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="recipe-section">
                <h4 style={{ marginBottom: 4 }}>Instructions</h4>
                {/* Explicitly force numbered list */}
                <ol
                  style={{
                    paddingLeft: 22,
                    margin: 0,
                    listStyleType: 'decimal',
                  }}
                >
                  {instructionList.map((step, idx) => {
                    const isCurrentStep =
                      cookingSession &&
                      cookingSession.current_step_index === idx;
                    return (
                      <li
                        key={idx}
                        style={{
                          fontSize: 14,
                          marginBottom: 4,
                          padding: '6px 8px',
                          backgroundColor: isCurrentStep
                            ? '#fff3cd'
                            : 'transparent',
                          borderLeft: isCurrentStep
                            ? '4px solid #a83232'
                            : '4px solid transparent',
                          borderRadius: 4,
                          fontWeight: isCurrentStep ? 600 : 400,
                          transition: 'all 0.3s ease',
                        }}
                      >
                        {step}
                      </li>
                    );
                  })}
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <h2 style={{ margin: 0, fontSize: 20 }}>
                Ask Sous Chef
              </h2>
              {cookingSession && (
                <button
                  type="button"
                  onClick={handleEndSession}
                  disabled={loading}
                  style={{
                    padding: '8px 16px',
                    borderRadius: 999,
                    border: '1px solid #a83232',
                    backgroundColor: '#a83232',
                    color: '#fff',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    fontSize: 14,
                    fontWeight: 600,
                    transition: 'all 0.2s ease',
                  }}
                  onMouseOver={(e) => !loading && (e.target.style.backgroundColor = '#8b2a2a')}
                  onMouseOut={(e) => !loading && (e.target.style.backgroundColor = '#a83232')}
                >
                  That&apos;s a wrap!
                </button>
              )}
            </div>
            <div style={{ fontSize: 13, color: '#666', marginBottom: 8 }}>
              Prompt suggestions:
              <ul style={{ margin: '4px 0 0 16px', padding: 0 }}>
                <li>"Can I substitute broccoli for green beans?"</li>
                <li>"How do I know when the chicken is cooked?"</li>
                <li>"Let&apos;s move on to the next step."</li>
              </ul>
            </div>

            <div
              className="chat-messages"
              style={{
                flexShrink: 0,
                height: 260,
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
              {/* Voice output settings */}
              <div
                className="voice-settings"
                style={{
                  display: 'flex',
                  justifyContent: 'flex-end',
                  alignItems: 'center',
                  gap: 12,
                  marginBottom: 8,
                  padding: '8px 12px',
                  backgroundColor: '#f9f9f9',
                  borderRadius: 6,
                  border: '1px solid #e5e5e5',
                }}
              >
                {availableVoices.length > 0 && (
                  <select
                    value={selectedVoice?.name || ''}
                    onChange={(e) => {
                      const voice = availableVoices.find(v => v.name === e.target.value);
                      setSelectedVoice(voice);
                      console.log('Voice changed to:', voice?.name);
                    }}
                    style={{
                      padding: '4px 8px',
                      borderRadius: 4,
                      border: '1px solid #ddd',
                      fontSize: 12,
                      cursor: 'pointer',
                      backgroundColor: '#fff',
                      maxWidth: 180,
                    }}
                    title="Select voice for Sous Chef"
                  >
                    {availableVoices
                      .filter(v => v.lang.startsWith('en'))
                      .map((voice) => (
                        <option key={voice.name} value={voice.name}>
                          {voice.name.split(' ').slice(0, 2).join(' ')}
                        </option>
                      ))}
                  </select>
                )}
                
                <label
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    fontSize: 13,
                    color: '#666',
                    cursor: 'pointer',
                    userSelect: 'none',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={autoPlayResponses}
                    onChange={(e) => {
                      setAutoPlayResponses(e.target.checked);
                      if (!e.target.checked) {
                        stopSpeaking();
                      }
                    }}
                    style={{ cursor: 'pointer' }}
                  />
                  Auto-play
                </label>

                {isSpeaking && (
                  <button
                    type="button"
                    onClick={stopSpeaking}
                    title="Stop speaking"
                    style={{
                      padding: '6px 12px',
                      borderRadius: 999,
                      border: '2px solid #ff6b6b',
                      backgroundColor: '#ff6b6b',
                      color: '#fff',
                      cursor: 'pointer',
                      fontSize: 12,
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <span style={{ fontSize: 14 }}>🔊</span>
                    Stop
                  </button>
                )}
              </div>
              
              <textarea
                value={currentMessage}
                onChange={(e) => setCurrentMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (!loading && currentMessage.trim()) {
                      chat();
                    }
                  }
                }}
                disabled={loading || isListening}
                placeholder={isListening ? "Listening... speak now" : "Ask SousChef to clarify an instruction, give cooking tips, or move on to the next step..."}
                style={{
                  width: '100%',
                  minHeight: 80,
                  maxHeight: 140,
                  resize: 'vertical',
                  marginBottom: 8,
                  padding: 8,
                  borderRadius: 6,
                  border: isListening ? '2px solid #dc3545' : '1px solid #ddd',
                  fontSize: 14,
                  boxSizing: 'border-box',
                  backgroundColor: isListening ? '#fff5f5' : '#fff',
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
                  {speechSupported && (
                    <button
                      type="button"
                      onClick={isListening ? stopListening : startListening}
                      disabled={loading}
                      title={isListening ? 'Stop listening' : 'Start voice input'}
                      style={{
                        padding: '6px 14px',
                        borderRadius: 999,
                        border: isListening ? '2px solid #dc3545' : '2px solid #a83232',
                        backgroundColor: isListening ? '#dc3545' : '#fff',
                        color: isListening ? '#fff' : '#a83232',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        fontSize: 13,
                        fontWeight: 600,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4,
                        transition: 'all 0.2s ease',
                      }}
                    >
                      <span style={{ fontSize: 14 }}>🎤</span>
                      {isListening ? 'Listening...' : 'Voice'}
                    </button>
                  )}
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
                    disabled={loading || !currentMessage?.trim() || isListening}
                    style={{
                      padding: '6px 18px',
                      borderRadius: 999,
                      border: '1px solid #a83232',
                      backgroundColor: loading ? '#f3a3a3' : '#a83232',
                      color: '#fff',
                      cursor:
                        loading || !currentMessage?.trim() || isListening
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

        {/* Session History Panel */}
        {sessionHistory.length > 0 && (
          <section
            className="session-history-panel"
            style={{
              marginTop: 24,
              border: '1px solid #e3e3e3',
              borderRadius: 10,
              padding: 16,
              backgroundColor: '#fafafa',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h2 style={{ margin: 0, fontSize: 18 }}>
                Previous Cooking Sessions
              </h2>
              <button
                type="button"
                onClick={async () => {
                  if (!confirm('Clear all cooking session history? This cannot be undone.')) return;
                  try {
                    await api.clearCookingSessionHistory();
                    setSessionHistory([]);
                  } catch (err) {
                    console.error('Failed to clear session history:', err);
                    alert('Failed to clear session history. Please try again.');
                  }
                }}
                style={{
                  padding: '6px 12px',
                  borderRadius: 6,
                  border: '1px solid #dc3545',
                  backgroundColor: '#fff',
                  color: '#dc3545',
                  cursor: 'pointer',
                  fontSize: 13,
                  fontWeight: 500,
                  transition: 'all 0.2s ease',
                }}
                onMouseOver={(e) => {
                  e.target.style.backgroundColor = '#dc3545';
                  e.target.style.color = '#fff';
                }}
                onMouseOut={(e) => {
                  e.target.style.backgroundColor = '#fff';
                  e.target.style.color = '#dc3545';
                }}
              >
                Clear All History
              </button>
            </div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                gap: 12,
              }}
            >
              {sessionHistory.map((session) => {
                const sessionDate = new Date(session.end_time);
                const formattedDate = sessionDate.toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                });
                const formattedTime = sessionDate.toLocaleTimeString('en-US', {
                  hour: 'numeric',
                  minute: '2-digit',
                  hour12: true,
                });

                return (
                  <div
                    key={session.id}
                    onClick={() => navigate(`/sous-chef/${session.recipe_id}`)}
                    style={{
                      padding: 12,
                      backgroundColor: '#fff',
                      border: '1px solid #ddd',
                      borderRadius: 8,
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                    onMouseOver={(e) => {
                      e.currentTarget.style.borderColor = '#a83232';
                      e.currentTarget.style.boxShadow = '0 2px 8px rgba(168, 50, 50, 0.1)';
                    }}
                    onMouseOut={(e) => {
                      e.currentTarget.style.borderColor = '#ddd';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  >
                    <div
                      style={{
                        fontSize: 14,
                        fontWeight: 600,
                        color: '#333',
                        marginBottom: 6,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {session.recipe_title}
                    </div>
                    <div
                      style={{
                        fontSize: 12,
                        color: '#666',
                        marginBottom: 4,
                      }}
                    >
                      Completed: {formattedDate}
                    </div>
                    <div
                      style={{
                        fontSize: 11,
                        color: '#999',
                      }}
                    >
                      {formattedTime}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
