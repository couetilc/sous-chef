import './style.css';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { useApi } from './useApi';
import IngredientsSelectMultiple from './ingredientsSelectMultiple'
import Recipe from './recipe'

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
  const [selectedRecipeId, setSelectedRecipeId] = useState(null);
  const navigate = useNavigate();

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
          return <Recipe recipe={recipe} triggerRefresh={updateList} />
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
