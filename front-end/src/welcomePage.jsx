import React from 'react';
import {useNavigate, Navigate} from 'react-router';
import './style.css'
import Home from './home.jsx';
import { useUser } from './useUser.jsx';
import { useState } from 'react';
import { useApi } from './useApi.jsx';

export default function WelcomePage(props) {
  const navigate = useNavigate();
  const { user } = useUser();
  const { api } = useApi();
  const [ boolFalse, setBoolFalse] = useState(false);
  const [ boolTrue, setBoolTrue] = useState(true);

  function navToHome() {
    //update onboarding skipped property
    api.setOnboardingStatus({boolFalse, boolTrue});
    return navigate("/home");
  }

  function navToOnboard() {
    api.setOnboardingStatus({boolFalse, boolFalse});
    return navigate("/onboarding");
  }
  
   
   return (
       <div className="centered-div">
         <h1> Welcome to Sous Chef! </h1>
         <p> Please complete the onboarding process, and tell us a little about yourself. </p>
         <div className="welcome-grid">
             <button
                 className="button"
                 onClick={navToOnboard}>
               Complete Onboarding Now
             </button>
             <button
                 className="button"
                 onClick={navToHome}>
               Maybe Later
             </button>
         </div>
       </div>
   );

}
