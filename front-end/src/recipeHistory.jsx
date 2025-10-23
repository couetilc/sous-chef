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
        <div class="recipe-history-recipe box">
          <h2>{recipe.title}</h2>
          <div class="recipe-history-summary">
            <img src={recipe.image_url} />
            <div class="recipe-history-meals">
              {meals.map(meal => {
                const { monthDay, year, time } = formatDate(meal.eaten_at)
                return (
                  <div class="recipe-history-meal">
                    <div class="meal-date">
                      <span class="date-label">meal eaten</span>
                      <span class="date-time">{time}</span>
                      <span class="date-full">{monthDay}, {year}</span>
                    </div>
                    <div class="meal-portion">
                      <span class="portion-label">portion</span>
                      <span class="portion-value">{formatPortion(meal.portion)}</span>
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
