import { useGET } from './useGET'

export default function RecipeHistory(props) {
  const data = useGET('recipeHistory')

  return (
    <div>
      <div>
        {data?.length > 0 && data.map(({ recipe, meals }) => (
          <div>
            <h2>{recipe.title}</h2>
            <div style={{flexFlow: 'row wrap', display: 'flex'}}>
              <img src={recipe.image_url} width="200px" height="150px" />
              {meals.map(meal => (
                <div>
                  <p>Eaten at: {meal.eaten_at}</p>
                  <p>Portion: {meal.portion}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
