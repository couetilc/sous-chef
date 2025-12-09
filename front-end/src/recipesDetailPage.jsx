import { useParams } from 'react-router'
import { useEffect, useState } from 'react'
import { useApi } from './useApi'
import { useGET } from './useGET'
import Recipe from './recipe'

// Convert decimal values close to n/3 into "n/3" (e.g., 0.6666 → 2/3, 1.6666 → 5/3)
function toThirdsFraction(value) {
  const val = parseFloat(value)
  if (!Number.isFinite(val)) return null

  // Leave clean integers alone (e.g., 1.0, 2.0)
  const roundedInt = Math.round(val)
  if (Math.abs(val - roundedInt) < 0.01) {
    return null
  }

  // Approximate as n/3
  const n = Math.round(val * 3)
  const approx = n / 3

  // Only accept if:
  // - it's actually a non-integer multiple of 1/3
  // - it's close enough to the original value
  if (n > 0 && n % 3 !== 0 && Math.abs(approx - val) < 0.02) {
    return `${n}/3`
  }

  return null
}

// Replace any decimal in the string that's close to n/3 with "n/3"
function formatIngredientAmountInString(text) {
  if (typeof text !== 'string') return text

  // Match any number-like token in the string
  const numberRegex = /-?\d*\.?\d+/g

  return text.replace(numberRegex, (match) => {
    const fraction = toThirdsFraction(match)
    return fraction || match
  })
}

// Recursively format all strings in the recipe object
function formatRecipeForDisplay(data) {
  if (Array.isArray(data)) {
    return data.map(formatRecipeForDisplay)
  }
  if (data && typeof data === 'object') {
    const result = {}
    for (const [key, value] of Object.entries(data)) {
      result[key] = formatRecipeForDisplay(value)
    }
    return result
  }
  if (typeof data === 'string') {
    return formatIngredientAmountInString(data)
  }
  return data
}

export default function RecipesDetailPage(props) {
  const { id } = useParams()
  const { api } = useApi()
  const tags = useGET('getTags')

  const [recipe, setRecipe] = useState()

  async function getRecipe() {
    api.getRecipeDetail({ id }).then(response => {
      const formatted = formatRecipeForDisplay(response)
      setRecipe(formatted)
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
