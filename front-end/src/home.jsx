import React from 'react';
import { useNavigate, Navigate } from 'react-router';
import './style.css';
import ChefHat from './chefhat.png';
import Nutrition from './nutrition.png';
import Recipe from './recipe.png';
import Inventory from './inventory.png';

// home page, only accesssed after a user has logged in

export default function Home(props) {
  const navigate = useNavigate();

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

  let user = props.user;
  let setUser = props.setUser;
  // if user is null, no user is logged in, redirect to the login page
  if ( user == null ) {
    console.log("null user, redirecting to login page");
    //alert("You are not logged in! Click ok to go to the Login Page");
    //return navigate("/login");
    return (
      <Navigate to="/login"/>
    )
  }
  console.log({user});
  return (
  <>
   <div className="centered-div">
     <p> Hello {user.username}! </p>
     <div className="home-grid">
       <div className="img-button-cont">
         <img src={ChefHat}/>
         <button
             className="btn"
             onClick={navToSousChef}>
           AI Sous Chef
         </button>
       </div>
       <div className="img-button-cont">
         <img src={Nutrition}/>
         <button
             className="btn"
             onClick={navToNutritionist}>
           Nutritionist
       </button>
       </div>
       <div className="img-button-cont">
         <img src={Recipe}/>
         <button
             className="btn"
             onClick={navToRecipes}>
           Recipes
       </button>
       </div>
       <div className="img-button-cont">
         <img src={Inventory}/>
         <button
             className="btn"
             onClick={navToInventory}>
           Inventory
         </button>
       </div>
     </div>
   </div>
   </>
  )
}
