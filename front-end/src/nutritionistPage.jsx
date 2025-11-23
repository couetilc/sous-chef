import './style.css';
import {useNavigate} from 'react-router';
import { useApi } from './useApi';
import { useEffect, useState, useRef, useMemo } from 'react';
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

function parseRecipeFromToolCall(toolCalls) {
  if (!toolCalls || toolCalls.length === 0) return null;

  console.log('parsing')

  const markReadyCall = toolCalls.findLast(tc => tc.tool_name === 'mark_recipe_ready');
  if (!markReadyCall || !markReadyCall.result) return null;

  try {
  console.log('found  parsing ', markReadyCall.result)
  console.log('found  json ', JSON.parse(markReadyCall.result))
    return JSON.parse(markReadyCall.result);
  } catch {
    return null;
  }
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
            {recipe.instructions.map((step, i) => (
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
  const messagesEndRef = useRef(null);

  // Find the most recent pending recipe from messages
  const pendingRecipe = useMemo(() => {
    // Look through messages in reverse to find the most recent mark_recipe_ready call
    for (let i = messages.length - 1; i >= 0; i--) {
      console.log('iter ', messages.length)
      console.log('i ', i)
      const msg = messages[i];
      console.log('msg ', msg )
      if (msg.role === 'assistant' && msg.tool_calls) {
        const recipe = parseRecipeFromToolCall(msg.tool_calls);
        console.log('recipe found ', recipe)
        if (recipe && recipe.status === 'pending_confirmation') {
          console.log('returning ', recipe)
          return recipe;
        }
      }
    }
    return null;
  }, [messages]);

  console.log({ pendingRecipe })

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

  // Auto-scroll to bottom when messages change or loading starts
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  async function chat() {
    if (!currentMessage?.trim()) return;

    setLoading(true);
    setError(false);
    setSavedRecipeId(null);

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
      setSavedRecipeId(null);
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
        setSavedRecipeId(response.recipe.id);
        // Refresh conversation to update the recipe status in tool calls
        const convResponse = await api.getConversation();
        if (convResponse.messages) {
          setMessages(convResponse.messages);
        }
      }
    } catch (err) {
      console.error('Save recipe error:', err);
      setError(true);
    } finally {
      setSaving(false);
    }
  }

  async function handleDiscardRecipe() {
    if (!confirm('Discard this recipe? This cannot be undone.')) return;

    setDiscarding(true);
    try {
      await api.discardInProgressRecipe();
      // Refresh conversation to update the recipe status
      const convResponse = await api.getConversation();
      if (convResponse.messages) {
        setMessages(convResponse.messages);
      }
    } catch (err) {
      console.error('Discard recipe error:', err);
      setError(true);
    } finally {
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
