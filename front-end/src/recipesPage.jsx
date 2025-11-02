import './style.css';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { useApi } from './useApi';

import SousChefLogo from './souschef-logo.png';

export default function Recipes() {
  const { api } = useApi();
  const [enteredName, setEnteredName] = useState('')
  const [filterFavorites, setFilterFavorites] = useState(false)
  const [page, setPage] = useState(1)
  const [recipes, setRecipes ] = useState();

  useEffect(() => {
    const param = { page }
    if (enteredName && enteredName != '') {
      param.title = enteredName
    }
    if (filterFavorites) {
      param.searchFavorite = 'True'
    }
    api.getRecipesFiltered(param).then(setRecipes)
  }, [api, enteredName, filterFavorites, page])

  const onFilterFavorites = () => {
    setFilterFavorites(!filterFavorites)
  }

  const clearFilters = () => {
    setEnteredName('')
    setFilterFavorites(false)
  }

  return (
    <div className="recipes-page">
      <h1>Recipe Page</h1>
      <div>
        <form onSubmit={e => {
          e.preventDefault()
          const form = new FormData(e.target)
          setEnteredName(form.get('recipeName'))
        }}>
          <input
            name="recipeName"
            placeholder='Search Recipe Name'
          ></input>
          <button type="submit">Search Name</button>
        </form>
      </div>
      <div>
        <button
          type="button"
          onClick={onFilterFavorites}
        >
          Filter by Favorites ({filterFavorites.toString()})
        </button>
      </div>
      <div>
        <button type="button" onClick={clearFilters}>Clear Filters</button>
      </div>
      <div>
        {recipes?.previous &&
          <button onClick={() => setPage(p => p - 1)}>previous page</button>}
        {recipes?.next &&
          <button onClick={() => setPage(p => p + 1)}>next page</button>}
      </div>
      <div>
        {recipes?.results.map(recipe => (
          <div key={recipe.id}>
            <div>{recipe.title}</div>
            <div>Ingredients:</div>
            <ul>{recipe.ingredients.split('|').map(ingredient => (
              <li>{ingredient.trim()}</li>
            ))}</ul>
            <div>Instructions:</div>
            <ul>{recipe.instructions.split('|').map(step => (
            <li>{step}</li>
            ))}</ul>
            {recipe.image_url &&
              <img width="200px" src={recipe.image_url} loading="lazy"></img>}
            {recipe.source_url &&
              <a href={recipe.source_url} loading="lazy">source</a>}
          </div>
        ))}
      </div>
    </div>
  )
}
