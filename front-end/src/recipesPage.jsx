import './style.css';
import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router';
import { useApi } from './useApi';
import SelectCuratedIngredients from './selectCuratedIngredients'
import Recipe from './recipe'
import { useGET } from './useGET'

import SousChefLogo from './souschef-logo.png';

export default function Recipes() {
  const { api } = useApi();
  const tags = useGET('getTags')
  const curatedIngredientsRef = useRef(null)
  const nameInputRef = useRef(null)
  const [enteredName, setEnteredName] = useState('')
  const [filterInventory, setFilterInventory] = useState(false)
  const [filterFavorites, setFilterFavorites] = useState(false)
  const [page, setPage] = useState(1)
  const [recipes, setRecipes ] = useState();
  const [ingredientFilterTrigger, setIngredientFilterTrigger] = useState(0)
  const [ count, setCount ] = useState(0);
  const [servingsMultipliers, setServingsMultipliers] = useState({});
  const [servingsInputs, setServingsInputs] = useState({});
  const [selectedRecipeId, setSelectedRecipeId] = useState(null);
  const navigate = useNavigate();

  // Separate state for active filters (what's being searched)
  const [activeFilters, setActiveFilters] = useState({
    name: '',
    inventory: false,
    favorites: false,
  })

  // Execute search with current filter values
  const executeSearch = useCallback(() => {
    const param = { page }
    if (activeFilters.name && activeFilters.name !== '') {
      param.title = activeFilters.name
    }
    if (activeFilters.inventory) {
      param.searchCuratedInventory = 'True'
    }
    if (activeFilters.favorites) {
      param.searchFavorite = 'True'
    }
    if (curatedIngredientsRef.current) {
      const curated_ingredients = curatedIngredientsRef.current.getSelectedIds()
      if (curated_ingredients.length > 0) {
        param.curated_ingredients = curated_ingredients
      }
    }
    api.getRecipesFiltered(param).then((result) => {
      setCount(result.count)
      return result
    }).then(setRecipes)
  }, [api, page, activeFilters])

  // Only auto-update on page change and initial load
  useEffect(() => {
    executeSearch()
  }, [executeSearch])

  const handleSearch = (e) => {
    e?.preventDefault()
    // Update active filters with current form values and increment trigger
    setActiveFilters(prev => ({
      name: enteredName,
      inventory: filterInventory,
      favorites: filterFavorites,
    }))
    setPage(1) // Reset to page 1 when searching
  }

  const clearFilters = () => {
    setEnteredName('')
    setFilterInventory(false)
    setFilterFavorites(false)
    setIngredientFilterTrigger(t => t + 1)
    if (nameInputRef.current) {
      nameInputRef.current.value = ''
    }
    // Clear and search
    setActiveFilters(prev => ({
      name: '',
      inventory: false,
      favorites: false,
    }))
    setPage(1)
  }

  // Helpers

  return (
    <div className="recipes-page">
      <h1>Recipe Page</h1>
      <h2>Displaying {count} recipes</h2>
      {/* Ready to Cook CTA appears at top of page when a recipe is selected */}
      {selectedRecipeId && (
        <div style={{ marginTop: 8, textAlign: 'center' }}>
          <button className="button-blue" onClick={() => navigate('/sous-chef')}>Ready to Cook?</button>
        </div>
      )}
      <div className="filter-bar">
        <form onSubmit={handleSearch}>
          <div>
            <label>Search by Recipe Name:
            <input
              ref={nameInputRef}
              className="text-input"
              name="recipeName"
              placeholder='Search'
              onChange={(e) => setEnteredName(e.target.value)}
            />
            </label>
          </div>

          <div>
            <label>Search by Ingredient:
            <SelectCuratedIngredients
              ref={curatedIngredientsRef}
              key={ingredientFilterTrigger}
              excludeInventory={false}
            />
            </label>
          </div>

          <div class="filter-checkboxes">
            <label>
              <input
                type="checkbox"
                checked={filterFavorites}
                onChange={(e) => setFilterFavorites(e.target.checked)}
              />
              Filter by Favorites
            </label>

            <label>
              <input
                type="checkbox"
                checked={filterInventory}
                onChange={(e) => setFilterInventory(e.target.checked)}
              />
              Filter by Inventory
            </label>
          </div>

          <div class="filter-buttons">
            <button className="button" type="submit">Search</button>
            <button className="button-blue" type="button" onClick={clearFilters}>Clear Filters</button>
          </div>
        </form>
      </div>
      <div className="paging">
        {recipes?.previous &&
          <button className="button" onClick={() => setPage(p => p - 1)}>previous page</button>}
        {recipes?.next &&
          <button className="button" onClick={() => setPage(p => p + 1)}>next page</button>}
      </div>
      <div className="recipes-list">
        {recipes?.results.map(recipe => {
          return <Recipe key={recipe.id} tags={tags} recipe={recipe} triggerRefresh={executeSearch} />
        })}
      </div>

      {/* Ready to Cook CTA appears after a recipe is selected */}
      {selectedRecipeId && (
        <div style={{ marginTop: 16 }}>
          <button className="button-blue" onClick={() => navigate('/sous-chef')}>Ready to Cook?</button>
        </div>
      )}
    </div>
  )
}
