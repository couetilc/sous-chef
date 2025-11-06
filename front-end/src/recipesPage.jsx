import './style.css';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { useApi } from './useApi';
import IngredientsSelectMultiple from './ingredientsSelectMultiple'

import SousChefLogo from './souschef-logo.png';

export default function Recipes() {
  const { api } = useApi();
  const [enteredName, setEnteredName] = useState('')
  const [filterInventory, setFilterInventory] = useState(false)
  const [filterFavorites, setFilterFavorites] = useState(false)
  const [page, setPage] = useState(1)
  const [recipes, setRecipes ] = useState();
  const [selectedOptions, setSelectedOptions] = useState([])
  const [ count, setCount ] = useState(0);
  const [servingsMultipliers, setServingsMultipliers] = useState({});
  const [servingsInputs, setServingsInputs] = useState({});

  const updateList = () => {
    const param = { page }
    if (enteredName && enteredName !== '') {
      param.title = enteredName
    }
    if (filterInventory) {
      param.searchInventory = 'True'
    }
    if (filterFavorites) {
      param.searchFavorite = 'True'
    }
    if (selectedOptions.length !== 0) {
      const ingredients = selectedOptions.map(option => option.value)
      param.ingredients = ingredients
    }

    api.getRecipesFiltered(param).then((result) => {
      setCount(result.count)
      return result
    }).then(setRecipes)
  }

  useEffect(updateList, [api, enteredName, filterFavorites, filterInventory, selectedOptions, page])

  const onFilterInventory = () => {
    setFilterInventory(!filterInventory)
  }

  const onFilterFavorites = () => {
    setFilterFavorites(!filterFavorites)
  }

  const clearFilters = () => {
    setEnteredName('')
    setFilterInventory(false)
    setFilterFavorites(false)
    setSelectedOptions([])
    document.querySelector('input[name="recipeName"]').value = '';
  }

  // Helpers
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

  // Handler to update multiplier for a recipe id
  const handleServingsChange = (recipeId, value) => {
    setServingsInputs(prev => ({ ...prev, [recipeId]: value }));
    const parsed = parseFloat(value);
    if (!isNaN(parsed) && parsed > 0) {
      setServingsMultipliers(prev => ({ ...prev, [recipeId]: parsed }));
    }
  };

  return (
    <div className="recipes-page">
      <h1>Recipe Page</h1>
      <h2>Displaying {count} recipes</h2>
      <div className="filter-bar">
        <div className="filter-name">
          <form onSubmit={e => {
            e.preventDefault()
            const form = new FormData(e.target)
            setEnteredName(form.get('recipeName'))
          }}>
            <input
              name="recipeName"
              placeholder='Search Recipe Name'
            ></input>
            <button className="button" type="submit">Search Name</button>
          </form>
        </div>
        <div className="filter-favorite">
          <button className="button"
            type="button"
            onClick={onFilterInventory}
          >
            Filter by Inventory ({filterInventory.toString()})
          </button>

          <button className="button"
            type="button"
            onClick={onFilterFavorites}
          >
            Filter by Favorites ({filterFavorites.toString()})
          </button>
        </div>
        <div className="filter-clear">
          <button className="button" type="button" onClick={clearFilters}>Clear Filters</button>
        </div>
      </div>
      <div>
        <IngredientsSelectMultiple selectedOptions={selectedOptions} setSelectedOptions={setSelectedOptions}/>
      </div>
      <div className="paging">
        {recipes?.previous &&
          <button className="button" onClick={() => setPage(p => p - 1)}>previous page</button>}
        {recipes?.next &&
          <button className="button" onClick={() => setPage(p => p + 1)}>next page</button>}
      </div>
      <div className="recipes-list">
        {recipes?.results.map(recipe => {
          const pricePer = formatCurrency(recipe.price_per_serving_usd)
          const priceTotal = formatCurrency(recipe.total_price_usd)

          return (
            <div key={recipe.id} className="recipe">
              <h3>{recipe.title}</h3>
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
                      value={servingsInputs[recipe.id] ?? servingsMultipliers[recipe.id] ?? 1}
                      onChange={(e) => handleServingsChange(recipe.id, e.target.value)}
                      style={{ width: '60px' }}
                    />
                    <ul>
                      <li>{"Calories: " + ((recipe.calories_per_serving || 0) * (servingsMultipliers[recipe.id] || 1)).toFixed(1)}</li>
                      <li>{"Fat: " + ((recipe.fat_g || 0) * (servingsMultipliers[recipe.id] || 1)).toFixed(1) + "g"}</li>
                      <li>{"Protein: " + ((recipe.protein_g || 0) * (servingsMultipliers[recipe.id] || 1)).toFixed(1) + "g"}</li>
                      <li>{"Carbs: " + ((recipe.carbs_g || 0) * (servingsMultipliers[recipe.id] || 1)).toFixed(1) + "g"}</li>
                    </ul>
                  </div>

                </div>
              </div>

              <div className="ingredients">
                <details>
                  <summary><h4>Ingredients:</h4></summary>
                  <ul className="ingredients-list">{recipe.ingredients.split('|').map((ingredient, i) => (
                    <li key={i}>{ingredient.trim()}</li>
                  ))}</ul>
                </details>
              </div>

              <div className="instructions" style={{ marginTop: '12px' }}>
                <details>
                  <summary><h4>Instructions:</h4></summary>
                  <ul>{recipe.instructions.split('|').map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}</ul>
                </details>
              </div>



              <button
                className={recipe.is_favorited ? "button-toggledOn" : "button"}
                onClick={() => {
                  api.updateFavoriteRecipe({ id: recipe.id })
                    .then(updateList())
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
        })}
      </div>
    </div>
  )
}
