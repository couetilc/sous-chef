import { useGET } from './useGET'

function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit'
  })
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
              {meals.map(meal => (
                <div class="recipe-history-meal">
                  <p>Eaten at: {formatDate(meal.eaten_at)}</p>
                  <p>Portion: {formatPortion(meal.portion)}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
