import { useState, useRef } from 'react'
import { useApi } from './useApi'
import { useNavigate } from 'react-router'

const formatCurrency = (val) => {
  const num = Number(val)
  if (!isFinite(num) || num <= 0) return null
  return `$${num.toFixed(2)}`
}

const hasCookTime = (t) => {
  if (t === null || t === undefined) return false
  const n = Number(t)
  return isFinite(n) && n > 0
}

export default function Recipe(props) {
  const recipe = props.recipe
  const { api } = useApi()
  const isDetailPage = props.isDetailPage
  const [editMode, setEditMode] = useState(false)
  const navigate = useNavigate()

  const [ingredients, setIngredients] = useState(props.recipe.ingredients)
  const [instructions, setInstructions] = useState(props.recipe.instructions)

  const [servings, setServings] = useState()

  const pricePer = formatCurrency(recipe.price_per_serving_usd)
  const priceTotal = formatCurrency(recipe.total_price_usd)
  async function submitChanges() {
    await api.updateCustomRecipe({id: recipe.id, ingredients: ingredients, instructions: instructions})
  }


  return (
    <div key={recipe.id} className="recipe">
      {isDetailPage &&
        <h3>
          {recipe.title} {editMode
            ? <>
                <button className="button" type="button" onClick = {submitChanges}>
                  Save
                </button> <button className="button-blue" type="button" onClick={
                  () => {
                    setEditMode(mode => !mode)
                    setIngredients(recipe.ingredients)
                    setInstructions(recipe.instructions)
                  }
                }>
                  Cancel
                </button>
              </>
            : <button className="button" type="button" onClick={
              () => setEditMode(mode => !mode)
            }>
              Edit
            </button>
          }
        </h3>
      }
      {!isDetailPage &&
        <h3>
          <a href={`/recipes/${recipe.id}/`}>
            {recipe.title}
          </a>
        </h3>
      }
      <button
                  className="button-blue"
                  onClick={() => navigate(`/sous-chef/${recipe.id}`)}
                >
                  Ready to cook?
                </button>
      <div className="image-ingredients">
        {recipe.image_url &&
          <img width="200px" src={recipe.image_url} loading="lazy" alt={recipe.title} />}

        <div className="image-side-panel">
          <div className="time">
            <h4>Time:</h4>
            <ul>
              <li>Prep: {Number(recipe.prep_time_min) || 0} min</li>
              {hasCookTime(recipe.cook_time_min) && (
                <li>Cook: {Number(recipe.cook_time_min)} min</li>
              )}
              <li>Total: {Number(recipe.total_time_min) || 0} min</li>
            </ul>
          </div>

          {/* New: Price section */}
          {(pricePer || priceTotal) && (
            <div className="price" style={{ marginTop: '8px' }}>
              <h4>Price:</h4>
              <ul>
                {pricePer && <li>Per serving: {pricePer}</li>}
                {priceTotal && <li>Total: {priceTotal}</li>}
              </ul>
            </div>
          )}

          <div className="servings">
            <h4>Servings: {recipe.servings}</h4>
          </div>

          <div className="nutrition">
            <h4>Nutrition Calculator:</h4>
            <br />
            <label htmlFor={`servings-${recipe.id}`} style={{ marginRight: '6px' }}>
              # of servings:
            </label>
            <input
              id={`servings-${recipe.id}`}
              type="number"
              min="1"
              step="0.5"
              value={servings ?? 1}
              onChange={(e) => setServings(e.target.value)}
              style={{ width: '60px' }}
            />
            <ul>
              <li>{"Calories: " + ((recipe.calories_per_serving || 0) * (servings || 1)).toFixed(1)}</li>
              <li>{"Fat: " + ((recipe.fat_g || 0) * (servings || 1)).toFixed(1) + "g"}</li>
              <li>{"Protein: " + ((recipe.protein_g || 0) * (servings || 1)).toFixed(1) + "g"}</li>
              <li>{"Carbs: " + ((recipe.carbs_g || 0) * (servings || 1)).toFixed(1) + "g"}</li>
            </ul>
          </div>

        </div>
      </div>

      <div className="ingredients">
        {isDetailPage &&
          <>
            <h4>Ingredients:</h4>
            {editMode
              ? <textarea
                  value={ingredients}
                  onChange={e => setIngredients(e.target.value)}
                />
              : <ul className="ingredients-list">{recipe.ingredients.split('|').map((ingredient, i) => (
                  <li key={i}>{ingredient.trim()}</li>
                ))}</ul>
            }
          </>
        }
        {!isDetailPage &&
          <details>
            <summary><h4>Ingredients:</h4></summary>
            <ul className="ingredients-list">{recipe.ingredients.split('|').map((ingredient, i) => (
              <li key={i}>{ingredient.trim()}</li>
            ))}</ul>
          </details>
        }
      </div>

      <div className="instructions" style={{ marginTop: '12px' }}>
        {isDetailPage &&
          <>
            <h4>Instructions:</h4>
            {editMode
              ? <textarea
                  value={instructions}
                  onChange={e => setInstructions(e.target.value)}
                />
              : <ul>{recipe.instructions.split('|').map((step, i) => (
                  <li key={i}>{step}</li>
                ))}</ul>
            }
          </>
        }
        {!isDetailPage &&
          <details>
            <summary><h4>Instructions:</h4></summary>
            <ul>{recipe.instructions.split('|').map((step, i) => (
              <li key={i}>{step}</li>
            ))}</ul>
          </details>
        }
      </div>



      <button
        className={recipe.is_favorited ? "button-toggledOn" : "button"}
        onClick={() => {
          api.updateFavoriteRecipe({ id: recipe.id })
            .then(props.triggerRefresh)
          // Page gets refetched every time you un/favorite a recipe.
          // Could avoid this by attaching state but leaving the current behavior.
        }}
      >
        {recipe.is_favorited ? '★ Unfavorite this recipe' : '☆ Favorite this recipe'}
      </button>

 
    
      {recipe.source_url &&
        <a className="source-url" href={recipe.source_url} target="_blank" rel="noreferrer">source</a>}
    </div>
  )
}
