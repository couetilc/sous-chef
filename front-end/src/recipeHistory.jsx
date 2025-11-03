import { useGET } from './useGET'
import { useState } from 'react'
import AddMealDialog from './addMealDialog'

function formatDate(dateString) {
  const date = new Date(dateString)
  const monthDay = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  const year = date.getFullYear()
  const time = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
  return { monthDay, year, time }
}

function formatServings(servings) {
  const num = parseFloat(servings)
  if (num === 1) return '1 serving'
  return `${num.toFixed(num % 1 === 0 ? 0 : 2)} servings`
}

export default function RecipeHistory(props) {
  const { data, refresh } = useGET('recipeHistory')
  const [active, setActive] = useState(null) // { cookedRecipeId, recipe }

  return (
    <div id="recipe-history">
      {data?.length > 0 && data.map(({ id, recipe, meals }) => ( // NOTE: use top-level id as cookedRecipeId
        <div key={id} className="recipe-history-recipe">
          <div className="recipe-history-recipe-title">
            <h2>{recipe.title}</h2>
            <button
              className="button"
              onClick={() => setActive({ cookedRecipeId: id, recipe })}
            >
              Add Meal
            </button>
          </div>

          <div className="recipe-history-summary">
            {recipe.image_url && <img src={recipe.image_url} alt={recipe.title} />}
            <div className="recipe-history-meals">
              {meals.map(meal => {
                const { monthDay, year, time } = formatDate(meal.eaten_at)
                return (
                  <div key={meal.id} className="recipe-history-meal">
                    <div className="meal-date">
                      <span className="date-label">meal eaten</span>
                      <span className="date-time">{time}</span>
                      <span className="date-full">{monthDay}, {year}</span>
                    </div>
                    <div className="meal-servings">
                      <span className="servings-value">{formatServings(meal.servings)}</span>
                      <span className="servings-label"> eaten</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      ))}

      {active && (
        <AddMealDialog
          recipe={active.recipe}
          cookedRecipeId={active.cookedRecipeId} // NOTE: pass cookedRecipeId for POST
          onClose={() => { setActive(null); refresh() }}
          // onSuccess: if your useGET exposes a refetch, you can call it here
          // onSuccess={() => refetch?.()}
        />
      )}
    </div>
  )
}
