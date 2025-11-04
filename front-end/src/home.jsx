import React from 'react';
import { useNavigate, Navigate } from 'react-router';
import './style.css';
import ChefHat from './chefhat.png';
import Nutrition from './nutrition.png';
import Recipe from './recipe.png';
import Inventory from './inventory.png';
import { useUser } from './useUser.jsx'

// home page, only accesssed after a user has logged in

export default function Home(props) {
  const navigate = useNavigate();
  const { user } = useUser();

  // navigation elements
  function navToSousChef() {
    return navigate("/sous-chef");
  }

  function navToNutritionist() {
    return navigate("/nutritionist");
  }

  function navToRecipes() {
    return navigate("/recipes");
  }

  function navToInventory() {
    return navigate("/inventory");
  }

  function navToLogout() {
    return navigate("/logout/");
  }

  // if user is null, no user is logged in, redirect to the login page
  if (!user) {
    return (
      <Navigate to="/login"/>
    )
  }
  console.log({user});
  return (
    <div className="home-page">
      <p> Hello {user.username}! </p>
      <div className="home-grid">
        <div className="grid-row">
          <div className="img-button-cont">
            <img src={ChefHat}/>
            <button
              className="button"
              onClick={navToSousChef}>
              AI Sous Chef
            </button>
          </div>
          <div className="img-button-cont">
            <img src={Nutrition}/>
            <button
              className="button"
              onClick={navToNutritionist}>
              Nutritionist
            </button>
          </div>
        </div>
        <div className="grid-row">
          <div className="img-button-cont">
            <img src={Recipe}/>
            <button
              className="button"
              onClick={navToRecipes}>
              Recipes
            </button>
          </div>
          <div className="img-button-cont">
            <img src={Inventory}/>
            <button
              className="button"
              onClick={navToInventory}>
              Inventory
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
