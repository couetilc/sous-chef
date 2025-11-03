import React, { useState, useEffect } from 'react';
import { useNavigate, Navigate } from 'react-router';
import './style.css';
import ChefHat from './chefhat.png';
import Nutrition from './nutrition.png';
import Recipe from './recipe.png';
import Inventory from './inventory.png';
import { useUser } from './useUser.jsx'
import { useApi } from './useApi.jsx';

// home page, only accesssed after a user has logged in


export default function Home(props) {
  const [onboarded, setOnboarded] = useState(false);
  const [skipped, setSkipped] = useState(false);
  

  useEffect(() => {
    //runs once on page mount
    async function getResponse() {
      response = await api.getOnboardingStatus();
      if ( response.ok ) {
        setOnboarded(response.onboarded);
        setSkipped(response.skipped);
      }
      else {
        alert("ERROR: Non-ok response from onboarding status fetch!");
      }
    }
  }, []);

  function OnboardWarning() {
    //optional onboarding warning for users that have skipped the onboarding process
    function navToOnboard() {
      const navigate = useNavigate();
    }

    if ( !onboarded && skipped ) {
      return (
        <button onClick={navToOnboard}>
          Onboard Now!
        </button>
      )
    }
    return null;
  }

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
  <>
   <div className="centered-div">
     <p> Hello {user.username}! </p>
     <OnboardWarning/>
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
