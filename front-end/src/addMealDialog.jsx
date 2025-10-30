import { useEffect, useMemo, useState } from 'react'

export default function AddMealDialog({ recipe, onClose, onConfirm }) {
  const [servingsEaten, setServingsEaten] = useState('1')
  const [ateAt, setAteAt] = useState(() => new Date().toISOString().slice(0, 16)) // YYYY-MM-DDTHH:mm

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

  // Heuristics:
  // - If recipe.nutrition_per_serving exists: use it directly for per-serving
  // - Else if recipe.nutrition_total & recipe.servings exist: derive per-serving
  const perServing = useMemo(() => {
    const nps = recipe?.nutrition_per_serving
    if (nps) return nps
    const nt = recipe?.nutrition_total
    const sv = parseFloat(recipe?.servings)
    if (nt && Number.isFinite(sv) && sv > 0) return scaleNutrition(nt, 1 / sv)
    return null
  }, [recipe])

  const servingsNumber = parseNumber(servingsEaten)
  const willLog = useMemo(() => {
    if (!perServing || servingsNumber <= 0) return null
    return scaleNutrition(perServing, servingsNumber)
  }, [perServing, servingsNumber])

  const totalRecipe = useMemo(() => {
    if (!perServing || !recipe?.servings) return null
    const sv = parseFloat(recipe.servings)
    if (!Number.isFinite(sv) || sv <= 0) return null
    return scaleNutrition(perServing, sv)
  }, [perServing, recipe])

  function handleConfirm() {
    if (!onConfirm) return
    onConfirm({
      recipeId: recipe.id,
      servings: servingsNumber,
      eaten_at: new Date(ateAt).toISOString(), // backend can handle timezone or you can keep local
    })
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
      onClick={(e) => {
        // close when clicking backdrop (but not when clicking inside dialog)
        if (e.target === e.currentTarget) onClose?.()
      }}
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

            {!perServing && (
              <div style={{ opacity: 0.8, fontSize: 14 }}>
                No nutrition attached to this recipe yet. Add <code>nutrition_per_serving</code> or
                <code> nutrition_total + servings</code> to enable the preview.
              </div>
            )}

            {perServing && (
              <>
                <section>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>Per serving</div>
                  <NutritionGrid data={perServing} />
                </section>

                <section>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>
                    Will be logged ({servingsNumber || 0} servings)
                  </div>
                  {willLog ? <NutritionGrid data={willLog} /> : <div style={{ opacity: 0.8 }}>—</div>}
                </section>

                {totalRecipe && (
                  <section>
                    <div style={{ fontWeight: 600, marginBottom: 4 }}>
                      Total recipe (all servings)
                    </div>
                    <NutritionGrid data={totalRecipe} />
                  </section>
                )}
              </>
            )}
          </div>

          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
            <button className="button" onClick={onClose} style={{ padding: '10px 14px' }}>
              Cancel
            </button>
            <button
              className="button primary"
              onClick={handleConfirm}
              disabled={!servingsNumber || servingsNumber <= 0}
              style={{
                padding: '10px 14px',
                opacity: (!servingsNumber || servingsNumber <= 0) ? 0.6 : 1
              }}
            >
              Log intake
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
  // turn protein_g -> protein (g), sodium_mg -> sodium (mg), calories stays calories
  if (k.endsWith('_g')) return `${k.replace('_g', '').replaceAll('_', ' ')} (g)`
  if (k.endsWith('_mg')) return `${k.replace('_mg', '').replaceAll('_', ' ')} (mg)`
  return k.replaceAll('_', ' ')
}
