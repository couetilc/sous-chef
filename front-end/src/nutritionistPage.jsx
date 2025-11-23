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

function parseRecipeOutcome(toolCalls) {
  if (!toolCalls || toolCalls.length === 0) return null;

  const markReadyCall = toolCalls.find(tc => tc.tool_name === 'mark_recipe_ready');
  if (!markReadyCall || !markReadyCall.result) return null;

  try {
    const result = JSON.parse(markReadyCall.result);
    // Only return if the recipe has been saved or discarded
    if (result.saved_recipe_id || result.discarded) {
      return result;
    }
    return null;
  } catch {
    return null;
  }
}

function RecipeOutcome({ toolCalls }) {
  const outcome = parseRecipeOutcome(toolCalls);
  if (!outcome) return null;

  const title = outcome.title || 'Untitled Recipe';

  if (outcome.saved_recipe_id) {
    return (
      <div className="recipe-outcome recipe-outcome-saved">
        <span className="recipe-outcome-icon">✓</span>
        <span className="recipe-outcome-text">
          <strong>{title}</strong> was saved.{' '}
          <a href={`/recipes/${outcome.saved_recipe_id}/`}>View Recipe</a>
        </span>
      </div>
    );
  }

  if (outcome.discarded) {
    return (
      <div className="recipe-outcome recipe-outcome-discarded">
        <span className="recipe-outcome-icon">✗</span>
        <span className="recipe-outcome-text">
          <strong>{title}</strong> was discarded.
        </span>
      </div>
    );
  }

  return null;
}

function RecipePreview({ recipe, onSave, onDiscard, saving, discarding }) {
  if (!recipe) return null;

  const hasCookTime = recipe.cook_time_min > 0;

  return (
    <div className="recipe-preview">
      <div className="recipe-preview-header">
        <h3>{recipe.title || 'Untitled Recipe'}</h3>
        <span className="recipe-preview-badge">Ready for Review</span>
      </div>

      <div className="recipe-preview-content">
        <div className="recipe-preview-meta">
          <div className="recipe-preview-times">
            <span>Prep: {recipe.prep_time_min || 0} min</span>
            {hasCookTime && <span>Cook: {recipe.cook_time_min} min</span>}
            <span>Total: {recipe.total_time_min || 0} min</span>
          </div>
          {recipe.servings > 0 && (
            <div className="recipe-preview-servings">
              Servings: {recipe.servings}
            </div>
          )}
        </div>

        <div className="recipe-preview-section">
          <h4>Ingredients</h4>
          <ul className="recipe-preview-ingredients">
            {recipe.ingredients.map((ing, i) => (
              <li key={i}>{ing.quantity} {ing.unit} {ing.name}</li>
            ))}
          </ul>
        </div>

        <div className="recipe-preview-section">
          <h4>Instructions</h4>
          <ol className="recipe-preview-instructions">
            {(recipe.instructions_list || recipe.instructions || []).map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </div>
      </div>

      <div className="recipe-preview-actions">
        <button
          type="button"
          className="button-blue"
          onClick={onDiscard}
          disabled={saving || discarding}
        >
          {discarding ? 'Discarding...' : 'Discard'}
        </button>
        <button
          type="button"
          className="button"
          onClick={onSave}
          disabled={saving || discarding}
        >
          {saving ? 'Saving...' : 'Save Recipe'}
        </button>
      </div>
    </div>
  );
}

function ToolCallsIndicator({ toolCalls }) {
  const [expanded, setExpanded] = useState(false);

  if (!toolCalls || toolCalls.length === 0) return null;

  const toolNames = toolCalls.map(tc => tc.tool_name);
  const uniqueTools = [...new Set(toolNames)];

  return (
    <div className="tool-calls-indicator">
      <button
        className="tool-calls-toggle"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        <span className="tool-calls-icon">🔧</span>
        <span className="tool-calls-summary">
          {uniqueTools.length === 1
            ? `Used ${uniqueTools[0]}`
            : `Used ${toolCalls.length} tool${toolCalls.length > 1 ? 's' : ''}`}
        </span>
        <span className={`tool-calls-chevron ${expanded ? 'expanded' : ''}`}>▼</span>
      </button>
      {expanded && (
        <div className="tool-calls-details">
          {toolCalls.map((tc, idx) => (
            <div key={idx} className="tool-call-item">
              <div className="tool-call-name">{tc.tool_name}</div>
              {tc.result && (
                <div className="tool-call-result">{tc.result}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Nutritionist() {
  const navigate = useNavigate();
  const { api } = useApi();
  const [currentMessage, setCurrentMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [saving, setSaving] = useState(false);
  const [discarding, setDiscarding] = useState(false);
  const [savedRecipeId, setSavedRecipeId] = useState(null);
  const [pendingRecipe, setPendingRecipe] = useState(null);
  const messagesEndRef = useRef(null);

  // Fetch conversation and in-progress recipe from API
  async function refreshInProgressRecipe() {
    try {
      const response = await api.getInProgressRecipe();
      if (response.recipe && response.recipe.status === 'pending_confirmation') {
        setPendingRecipe(response.recipe);
      } else {
        setPendingRecipe(null);
      }
    } catch (err) {
      console.error('Failed to fetch in-progress recipe:', err);
      setPendingRecipe(null);
    }
  }

  // Fetch conversation and pending recipe on mount
  useEffect(() => {
    async function loadData() {
      try {
        const response = await api.getConversation();
        if (response.messages) {
          setMessages(response.messages);
        }
      } catch (err) {
        console.error('Failed to load conversation:', err);
      }
      await refreshInProgressRecipe();
    }
    loadData();
  }, [api]);

  // Auto-scroll to bottom when messages change or loading starts
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  async function chat(messageOverride) {
    // If messageOverride is not a string (e.g., click event), ignore it
    const messageToSend = typeof messageOverride === 'string' ? messageOverride : currentMessage;
    if (!messageToSend?.trim()) return;

    setLoading(true);
    setError(false);
    setSavedRecipeId(null);

    try {
      const response = await api.nutritionistChat({ message: messageToSend });
      setMessages(response.messages);
      // Only clear input if we used the state value (not a programmatic string override)
      if (typeof messageOverride !== 'string') {
        setCurrentMessage('');
      }
      // Refresh in-progress recipe in case AI called mark_recipe_ready
      await refreshInProgressRecipe();
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
      setSavedRecipeId(null);
      setPendingRecipe(null);
    } catch (err) {
      console.error('Clear error:', err);
      setError(true);
    }
  }

  async function handleSaveRecipe() {
    setSaving(true);
    try {
      const response = await api.saveInProgressRecipe();
      if (response.success && response.recipe) {
        setPendingRecipe(null);
        setSaving(false);
        // Send a message to the AI so it knows the recipe was saved
        await chat('I saved the recipe.');
      }
    } catch (err) {
      console.error('Save recipe error:', err);
      setError(true);
      setSaving(false);
    }
  }

  async function handleDiscardRecipe() {
    if (!confirm('Discard this recipe? This cannot be undone.')) return;

    setDiscarding(true);
    try {
      await api.discardInProgressRecipe();
      setPendingRecipe(null);
      setDiscarding(false);
      // Send a message to the AI so it knows the recipe was discarded
      await chat('I discarded the recipe.');
    } catch (err) {
      console.error('Discard recipe error:', err);
      setError(true);
      setDiscarding(false);
    }
  }

  return (
    <div className="nutritionist-page">
      <h1>NUTRITIONIST</h1>

      <div className="chat-messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            {msg.role === 'assistant' && (
              <ToolCallsIndicator toolCalls={msg.tool_calls} />
            )}
            <div className="message-content">
              {msg.role === 'assistant' ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {msg.content}
                </ReactMarkdown>
              ) : (
                msg.content
              )}
            </div>
            {msg.role === 'assistant' && (
              <RecipeOutcome toolCalls={msg.tool_calls} />
            )}
            <div className="message-time">{formatTime(msg.created_at)}</div>
          </div>
        ))}
        {loading && (
          <div className="loading-indicator">Thinking...</div>
        )}
        {pendingRecipe && !savedRecipeId && (
          <RecipePreview
            recipe={pendingRecipe}
            onSave={handleSaveRecipe}
            onDiscard={handleDiscardRecipe}
            saving={saving}
            discarding={discarding}
          />
        )}
        {savedRecipeId && (
          <div className="recipe-saved-notice">
            Recipe saved successfully!{' '}
            <a href={`/recipes/${savedRecipeId}/`}>View Recipe</a>
          </div>
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
