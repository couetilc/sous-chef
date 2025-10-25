import React form 'react';
import {useNavigate, Navigate } from 'react-router';
import'./style.css'
import Home from './home.jsx';
import { useUser } from './useUser.jsx';
import {useState } from 'react';

export default function Onboarding(props) {
  const navigate = useNavigate();
  const {user } = useUser();
  function navToHome() {
    return navigate("/home");
  }

    return (
      <div className="centered-div">
        <h1> Onboarding </h1>
        <div> className="onboard-div">
          
        </div>
      </div>
    );
  }
}
