import React from 'react';
import {useNavigate, Navigate } from 'react-router';
import './style.css'
import Home from './home.jsx';
import { useUser } from './useUser.jsx';
import DietComponent from './settingsDietPreference';
import RestrictedIngredientComponent from './settingsRestrictedIngredients.jsx';
import { useState } from 'react';
import { useApi } from './useApi.jsx';

export default function Onboarding(props) {
  const navigate = useNavigate();
  const { user } = useUser();
  const { api } = useApi();

  function navToHome() {
    return navigate("/home");
  }
  function navToHealthOnboard() {
    return navigate("/onboard-health");
  }

  return (
    <div className="centered-div">
      <h1> Onboarding </h1>
      <DietComponent> </DietComponent>
        <RestrictedIngredientComponent> </RestrictedIngredientComponent>
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
       <button className="continue-btn" onClick ={navToHealthOnboard}>
         Continue
       </button>
      </div>
    </div>
  );
}
