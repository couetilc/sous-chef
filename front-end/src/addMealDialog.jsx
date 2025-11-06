import { useEffect, useMemo, useRef, useState } from 'react'
import { useApi } from './useApi'

export default function AddMealDialog({ recipe, cookedRecipeId, onClose, onSuccess }) {
  const [servingsEaten, setServingsEaten] = useState('1')
  const [ateAt, setAteAt] = useState(() => new Date(
        new Date().getTime() - new Date().getTimezoneOffset() * 60000
      ).toISOString().slice(0, 16)) // YYYY-MM-DDTHH:mm
  const {api} = useApi()

  // Preview (GET) state
  const [preview, setPreview] = useState(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewError, setPreviewError] = useState(null)

  // POST state
  const [submitting, setSubmitting] = useState(false)

  const debounceRef = useRef(null)
  const abortRef = useRef(null)

  useEffect(() => {
    // lock background scroll while dialog is open
    const original = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = original }
  }, [])

  function parseNumber(v) {
    const n = parseFloat(v)
    return Number.isFinite(n) && n > 0 ? n : 0
  }

  function scaleNutrition(nutri, factor) {
    if (!nutri || typeof nutri !== 'object') return null
    const out = {}
    for (const k of Object.keys(nutri)) {
      const val = parseFloat(nutri[k])
      out[k] = Number.isFinite(val) ? +(val * factor).toFixed(2) : nutri[k]
    }
    return out
  }

  // Local fallback per-serving (only used if backend preview fails)
  const perServingLocal = useMemo(() => {
    const nps = recipe?.nutrition_per_serving
    if (nps) return nps
    const nt = recipe?.nutrition_total
    const sv = parseFloat(recipe?.servings)
    if (nt && Number.isFinite(sv) && sv > 0) return scaleNutrition(nt, 1 / sv)
    return null
  }, [recipe])

  const servingsNumber = parseNumber(servingsEaten)

  // === GET preview from backend whenever servings change ===
  useEffect(() => {
    if (!recipe?.id || servingsNumber <= 0) {
      setPreview(null)
      setPreviewError(null)
      return
    }

    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      if (abortRef.current) abortRef.current.abort()
      abortRef.current = new AbortController()

      setPreviewLoading(true)
      setPreviewError(null)

      fetch(`/api/recipes/${recipe.id}/nutrition/?servings=${encodeURIComponent(servingsNumber)}`, {
        method: 'GET',
        credentials: 'include',
        signal: abortRef.current.signal,
      })
        .then(async (res) => {
          if (!res.ok) throw new Error(`HTTP ${res.status}`)
          return res.json()
        })
        .then((json) => setPreview(json?.nutrition ?? null))
        .catch((err) => {
          if (err.name !== 'AbortError') {
            setPreview(null)
            setPreviewError(err.message || 'Failed to fetch preview')
          }
        })
        .finally(() => setPreviewLoading(false))
    }, 250)

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
      if (abortRef.current) abortRef.current.abort()
    }
  }, [recipe?.id, servingsNumber])

  const willLogLocal = useMemo(() => {
    if (!perServingLocal || servingsNumber <= 0) return null
    return scaleNutrition(perServingLocal, servingsNumber)
  }, [perServingLocal, servingsNumber])

  const effectivePreview = preview ?? willLogLocal

  async function handleConfirm() {
    if (servingsNumber <= 0 || submitting) return
    setSubmitting(true)
    try {
      // Endpoint: POST /api/cooked-recipes/<cooked_recipe_id>/meals/
      // Body: { servings, eaten_at }

      const eaten_at = new Date(
        new Date(ateAt).getTime()
      ).toISOString()

      const res = await api.fetch(`/api/recipe_history/${cookedRecipeId}/meal/`, {

        body: JSON.stringify({
          servings: servingsNumber,
          eaten_at,
        }),
      })
      // Placeholder behavior: just log the response; you can replace this with toasts/state
      if (!res.ok) {
        console.error('Log intake failed', res.status)
      } else {
        const json = await res.json().catch(() => ({}))
        console.log('Log intake success:', json)
        onSuccess?.(json)
      }
      onClose?.()
    } catch (err) {
      console.error('Log intake error:', err)
      onClose?.()
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="add-meal-backdrop"
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose?.() }}
    >
      <div
        className="add-meal-card"
        style={{
          width: 'min(640px, 92vw)',
          background: 'var(--bg, #111)',
          color: 'var(--fg, #eee)',
          borderRadius: '12px',
          padding: '20px',
          boxShadow: '0 10px 30px rgba(0,0,0,0.3)',
          border: '1px solid rgba(255,255,255,0.08)'
        }}
      >
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 12 }}>
          {recipe?.image_url && (
            <img
              src={recipe.image_url}
              alt={recipe?.title || 'recipe'}
              style={{ width: 54, height: 54, objectFit: 'cover', borderRadius: 8 }}
            />
          )}
          <div style={{ flex: 1 }}>
            <h3 style={{ margin: 0 }}>{recipe?.title || 'Recipe'}</h3>
            {Number.isFinite(parseFloat(recipe?.servings)) && (
              <div style={{ opacity: 0.8, fontSize: 13 }}>
                {parseFloat(recipe.servings)} total servings
              </div>
            )}
          </div>
          <button className="button" onClick={onClose} aria-label="Close" style={{ padding: '6px 10px' }}>
            ✕
          </button>
        </div>

        <div style={{ display: 'grid', gap: 16 }}>
          <label style={{ display: 'grid', gap: 6 }}>
            <span>How many servings did you eat?</span>
            <input
              type="number"
              inputMode="decimal"
              min="0"
              step="0.25"
              value={servingsEaten}
              onChange={(e) => setServingsEaten(e.target.value)}
              style={{
                padding: '10px 12px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.14)',
                background: 'transparent', color: 'inherit'
              }}
            />
          </label>

          <label style={{ display: 'grid', gap: 6 }}>
            <span>Date & time</span>
            <input
              type="datetime-local"
              value={ateAt}
              onChange={(e) => setAteAt(e.target.value)}
              style={{
                padding: '10px 12px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.14)',
                background: 'transparent', color: 'inherit'
              }}
            />
          </label>

          <div
            style={{
              display: 'grid',
              gap: 12,
              padding: 12,
              borderRadius: 10,
              border: '1px solid rgba(255,255,255,0.08)',
              background: 'rgba(255,255,255,0.03)'
            }}
          >
            <strong>Nutrition preview</strong>

            {previewLoading && <div style={{ opacity: 0.8, fontSize: 14 }}>Loading preview…</div>}
            {previewError && <div style={{ color: '#f66', fontSize: 14 }}>Error: {previewError}</div>}

            {!previewLoading && !effectivePreview && (
              <div style={{ opacity: 0.8, fontSize: 14 }}>
                No nutrition available yet for this recipe.
              </div>
            )}

            {!previewLoading && effectivePreview && (
              <>
                <section>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>
                    Will be logged ({servingsNumber || 0} servings)
                  </div>
                  <NutritionGrid data={effectivePreview} />
                </section>
              </>
            )}
          </div>

          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
            <button className="button" onClick={onClose} style={{ padding: '10px 14px' }} disabled={submitting}>
              Cancel
            </button>
            <button
              className="button primary"
              onClick={handleConfirm}
              disabled={!servingsNumber || servingsNumber <= 0 || submitting || !cookedRecipeId}
              style={{
                padding: '10px 14px',
                opacity: (!servingsNumber || servingsNumber <= 0 || !cookedRecipeId) ? 0.6 : 1
              }}
            >
              {submitting ? 'Logging…' : 'Log intake'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function NutritionGrid({ data }) {
  const entries = Object.entries(data || {})
    .filter(([, v]) => typeof v === 'number' || typeof v === 'string')

  if (!entries.length) return <div style={{ opacity: 0.8 }}>—</div>

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, minmax(0,1fr))',
        gap: 8,
        fontSize: 14
      }}
    >
      {entries.map(([k, v]) => (
        <div key={k} style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '8px 10px', borderRadius: 8, background: 'rgba(255,255,255,0.04)'
        }}>
          <span style={{ opacity: 0.85, textTransform: 'capitalize' }}>{formatKey(k)}</span>
          <span style={{ fontVariantNumeric: 'tabular-nums' }}>{v}</span>
        </div>
      ))}
    </div>
  )
}

function formatKey(k) {
  if (k.endsWith('_g')) return `${k.replace('_g', '').replaceAll('_', ' ')} (g)`
  if (k.endsWith('_mg')) return `${k.replace('_mg', '').replaceAll('_', ' ')} (mg)`
  return k.replaceAll('_', ' ')
}
