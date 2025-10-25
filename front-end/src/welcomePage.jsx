import React from 'react';
import {useNavigate, Navigate} from 'react-router';
import './style.css'
import Home from './home.jsx';
import { useUser } from './useUser.jsx';
import { useState } from 'react';

export default function WelcomePage(props) {
  const navigate = useNavigate();
  const { user } = useUser();

  function navToHome() {
    return navigate("/home");
  }

  function navToOnboard() {
    return navigate("/onboarding");
  }
   
  /*
   * If user has already done onboarding
   */
   //navToHome();


   return (
       <div className="centered-div">
         <h1> Welcome to Sous Chef! </h1>
         <p> Please complete the onboarding process, and tell us a little about yourself. </p>
         <div className="welcome-grid">
           <div className="img-button-cont">
             <button
                 className="btn"
                 onClick={navToOnboard}>
               Complete Onboarding Now
             </button>
           </div>
           <div className="img-button-cont">
             <button
                 className="btn"
                 onClick={navToHome}>
               Maybe Later
             </button>
           </div>
         </div>
       </div>
   );

}
