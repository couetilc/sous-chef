import { useGET } from './useGET'

function formatDate(dateString) {
  const date = new Date(dateString)
  const monthDay = date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric'
  })
  const year = date.getFullYear()
  const time = date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit'
  })
  return { monthDay, year, time }
}

function formatPortion(portion) {
  return `${Math.round(portion * 100)}%`
}

export default function RecipeHistory(props) {
  const data = useGET('recipeHistory')

  return (
    <div id="recipe-history">

      {data?.length > 0 && data.map(({ recipe, meals }) => (
        <div key={recipe.id} className="recipe-history-recipe">
          <div className="recipe-history-recipe-title">
            <h2>{recipe.title}</h2>
            <button className="button">Add Meal</button>
          </div>
          <div className="recipe-history-summary">
            <img src={recipe.image_url} />
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
                    <div className="meal-portion">
                      <span className="portion-value">{formatPortion(meal.portion)}</span>
                      <span className="portion-label">portion</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
