import React from 'react';
import {useNavigate, Navigate } from 'react-router';
import './style.css'
import Home from './home.jsx';
import { useUser } from './useUser.jsx';
import DietComponent from './settingsDietPreference';
import { useState } from 'react';

export default function Onboarding(props) {
  const navigate = useNavigate();
  const {user } = useUser();
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
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
       <button className="continue-btn" onClick ={navToHealthOnboard}>
         Continue
       </button>
      </div>
    </div>
  );
}
