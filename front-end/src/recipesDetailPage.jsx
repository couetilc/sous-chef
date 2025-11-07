import { useParams } from 'react-router'
import { useEffect, useState } from 'react'
import { useApi } from './useApi'
import { useGET } from './useGET'
import Recipe from './recipe'

export default function RecipesDetailPage(props) {
  const { id } = useParams()
  const { api } = useApi()
  const tags = useGET('getTags')

  const [recipe, setRecipe] = useState()

  async function getRecipe() {
    api.getRecipeDetail({ id }).then(response => {
      setRecipe(response)
    })
  }

  useEffect(() => {
    getRecipe()
  }, [])

  return (
    <div className="recipe-detail-page">
      {recipe && <Recipe tags={tags} recipe={recipe} isDetailPage triggerRefresh={getRecipe} /> }
    </div>
  )
}
