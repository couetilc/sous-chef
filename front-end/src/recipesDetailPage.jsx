import { useParams } from 'react-router'
import { useEffect, useState } from 'react'
import { useApi } from './useApi'
import Recipe from './recipe'

export default function RecipesDetailPage(props) {
  const { id } = useParams()
  const { api } = useApi()

  const [recipe, setRecipe] = useState()

  useEffect(() => {
    api.getRecipeDetail({ id }).then(response => {
      setRecipe(response)
    })
  }, [])

  return (
    <div className="recipe-detail-page">
      {recipe && <Recipe recipe={recipe} isDetailPage /> }
    </div>
  )
}
