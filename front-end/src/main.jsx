import './style.css'
import { createRoot } from 'react-dom/client'
import { useEffect, useState } from 'react'

import SousChefLogo from './souschef-logo.png';
import Login from './login.jsx';
import Home from './home.jsx';
import SousChef from './souschefPage.jsx';
import Nutritionist from './nutritionPage.jsx';
import Recipes from './recipesPage.jsx';
import Inventory from './inventory.jsx';
import SettingsPage from './settingsPage.jsx';
import CreateAccount from './createAccount.jsx';
import WelcomePage from './welcomePage.jsx';
import HeaderBanner from './headerBanner.jsx';
import LogoutPage from './logoutPage';
import PrivatePage from './privatePage';

import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import { Link } from 'react-router';
import { useNavigate, useLocation } from 'react-router';
import { StrictMode } from 'react';
import { ApiProvider } from './useApi';
import { UserProvider, useUser } from './useUser';

export default function App(props) {
  const navigate = useNavigate();

  function IsLoggedIn() {
    let isLogged = false;
    if ( curUser == null ) {
      isLogged = true;
    }
    //navigate to home page if user is logged in
    if ( isLogged == true ) {
      return navigate("/home");
    }
    //navigate to login page if user isn't logged in
    return navigate("/login");
  }

  const home = <PrivatePage><Home /></PrivatePage>
  const souschef = <PrivatePage><SousChef /></PrivatePage>
  const nutritionist = <PrivatePage><Nutritionist /></PrivatePage>
  const recipes = <PrivatePage><Recipes /></PrivatePage>
  const inventory = <PrivatePage><Inventory /></PrivatePage>
  const settings = <PrivatePage><SettingsPage /></PrivatePage>
  const welcome = <PrivatePage><WelcomePage /></PrivatePage>
  const onboard = <PrivatePage><WelcomePage /></PrivatePage>

  return (
    <>
      <div className="app-container">
        <HeaderBanner />
        <Routes>
          {/* private pages */}
          <Route path="home" element={home} />
          <Route path="sous-chef" element={souschef} />
          <Route path="nutritionist" element={nutritionist} />
          <Route path="recipes" element={recipes} />
          <Route path="inventory" element={inventory} />
          <Route path="settings" element={settings} />
          <Route path="welcome" element={welcome} />

          {/* public pages */}
          <Route path="login" element={<Login />} />
          <Route path="create-account" element={<CreateAccount />} />
          <Route path="logout" element={<LogoutPage />} />
          <Route path="/" element={<Login />} />
        </ Routes>
      </div>
    </>
  )
}

const root = createRoot(document.getElementById('root'))
root.render(
  <StrictMode>
  <BrowserRouter>
  <ApiProvider>
  <UserProvider>
    <App />
  </UserProvider>
  </ApiProvider>
  </BrowserRouter>
  </StrictMode>
)
