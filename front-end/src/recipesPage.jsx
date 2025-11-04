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
    document.querySelector('input[name="recipeName"]').value = '';
  }

  return (
    <div className="recipes-page">
      <h1>Recipe Page</h1>
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
            onClick={onFilterFavorites}
          >
            Filter by Favorites ({filterFavorites.toString()})
          </button>
        </div>
        <div className="filter-clear">
          <button className="button" type="button" onClick={clearFilters}>Clear Filters</button>
        </div>
      </div>
      <div className="paging">
        {recipes?.previous &&
          <button className="button" onClick={() => setPage(p => p - 1)}>previous page</button>}
        {recipes?.next &&
          <button className="button" onClick={() => setPage(p => p + 1)}>next page</button>}
      </div>
      <div className="recipes-list">
        {recipes?.results.map(recipe => (
          <div key={recipe.id} className="recipe">
            <h3>{recipe.title}</h3>
            <div className="image-ingredients">
              {recipe.image_url &&
                <img width="200px" src={recipe.image_url} loading="lazy"></img>}
              <div className="ingredients">
                <h4>Ingredients:</h4>
                <ul className="ingredients-list">{recipe.ingredients.split('|').map((ingredient, i) => (
                  <li key={i}>{ingredient.trim()}</li>
                ))}</ul>
              </div>
            </div>
            <div className="instructions">
              <h4>Instructions:</h4>
              <ul>{recipe.instructions.split('|').map((step, i) => (
              <li key={i}>{step}</li>
              ))}</ul>
            </div>
            <button 
              className={recipe.is_favorited ? "button-toggledOn" : "button"}
              onClick = {() => {
                
              }}
            >
                {recipe.is_favorited ? 'Unfavorite this recipe' : 'Favorite this recipe'}
            </button>
            {recipe.source_url &&
              <a className="source-url" href={recipe.source_url}>source</a>}
          </div>
        ))}
      </div>
    </div>
  )
}
