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

  const updateList = () => {
    const param = { page }
    if (enteredName && enteredName != '') {
      param.title = enteredName
    }
    if (filterInventory) {
      param.searchInventory = 'True'
    }
    if (filterFavorites) {
      param.searchFavorite = 'True'
    }
    if (selectedOptions.length != 0) {
      const ingredients = selectedOptions.map(option => option.value)
      console.log(ingredients)
      param.ingredients = ingredients
    }

    api.getRecipesFiltered(param).then( (result) => {
      setCount(result.count)
      return result
    }).then(setRecipes)
  }

  useEffect(updateList, [api, enteredName, filterFavorites, page])

  const onFilterInventory= () => {
    setFilterInventory(!filterInventory)
  }

  const onFilterFavorites = () => {
    setFilterFavorites(!filterFavorites)
  }

  const clearFilters = () => {
    setEnteredName('')
    setFilterFavorites(false)
    setSelectedOptions([])
    document.querySelector('input[name="recipeName"]').value = '';
  }

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
            <br></br>
            <br></br>
            <div className="servings">
              <h4>Servings:</h4>
              <ul>
                <li>{recipe.servings}</li>
              </ul>
            </div>
            <br></br>
            <div className="nutrition">
              <h4>Nutrition (per serving):</h4>
              <ul>
                <li>{"Calories: " + recipe.calories_per_serving}</li>
                <li>{"Fat: " + recipe.fat_g + "g"}</li>
                <li>{"Protein: " + recipe.protein_g + "g"}</li>
                <li>{"Carbs: " + recipe.carbs_g + "g"}</li>
              </ul>
            </div>
            <button 
              className={recipe.is_favorited ? "button-toggledOn" : "button"}
              onClick = {() => {
                api.updateFavoriteRecipe({id: recipe.id})
                .then(updateList())
                // Page gets refetched every time you un/favorite a recipe.
                // Could avoid this by attaching state but I was having trouble implementing it - might return later on
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
