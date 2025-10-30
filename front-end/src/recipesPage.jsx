import './style.css';
import { useState } from 'react';
import { useNavigate } from 'react-router';

import SousChefLogo from './souschef-logo.png';

export default function Recipes() {

  const [enteredName, setEnteredName] = useState('')
  const [filterFavorites, setFilterFavorites] = useState(false)

  const onFilterFavorites = () => {
    setFilterFavorites(!filterFavorites)
    console.log("pressed")
  }

  const clearFilters = () => {
    console.log("clear filters")
    setEnteredName('')
    setFilterFavorites(false)
  }

  const sendSearchRequest = () => {
    
  }

  return (
    <div className="centered-div">
      <div>
        <h1> RECIPES </h1>
        <p> Welcome to the Recipes Interface page!</p>
        <p> This is still under development, please come back later!</p>
      </div>
        <h1> Recipe Filters</h1>
      <div className='recipeFilterGrid'>
          <div className='name'>
            <input name="recipeName" value={enteredName} onChange={e => setEnteredName(e.target.value)} placeholder='Search Recipe Name'></input>
          </div>
          <div className='favorite'>
            <button type="button" onClick={onFilterFavorites}>{`Filter by Favorites (${filterFavorites})`}</button>
          </div>
          <div name='clear'>
            <button type="button" onClick={clearFilters}>Clear Filters</button>
          </div>
          <div name='search'>
            <button type="button" onClick={sendSearchRequest}>Search</button>
          </div>
      </div>
    </div>
  )
}
