import './style.css'
import { createRoot } from 'react-dom/client'
import { useEffect, useState } from 'react'

import CurvedEdge from './curvedEdge';
import SousChefLogo from './souschef-logo.png';
import Login from './login.jsx';
import Home from './home.jsx';
import SousChef from './souschefPage.jsx';
import Nutritionist from './nutritionPage.jsx';
import Recipes from './recipesPage.jsx';
import Inventory from './inventory.jsx';
import SettingsPage from './settingsPage.jsx';
import CreateAccount from './createAccount.jsx';
import LogoutPage from './logoutPage';
import PrivatePage from './privatePage';
import RecipeHistory from './recipeHistory';

import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import { Link } from 'react-router';
import { useNavigate, useLocation } from 'react-router';
import { StrictMode } from 'react';
import { ApiProvider } from './useApi';
import { UserProvider, useUser } from './useUser';

export default function App(props) {
  const navigate = useNavigate();
  const curLocation = useLocation();

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
  const history = <PrivatePage><RecipeHistory /></PrivatePage>

  return (
    <>
      <div className="app-container">
        <div className="left-menu">
          {/* left menu content */}
          {( curLocation.pathname.localeCompare("/") == 0 ||
             curLocation.pathname.localeCompare("/login/") == 0 ||
             curLocation.pathname.localeCompare("/create-account/") == 0)
             ? <img className="sous-chef-logo" src={SousChefLogo} height="300px"/>
             : <header className="navigation-menu">
                <a className="nav-link-home" href="/home">
                  <img className="sous-chef-logo" src={SousChefLogo} width="150px"/>
                </a>
                <nav>
                  <ul>
                    <li><a href="/home">Home</a></li>
                    <li><a href="/sous-chef">Sous Chef</a></li>
                    <li><a href="/nutritionist">Nutritionist</a></li>
                    <li><a href="/recipes">Recipes</a></li>
                    <li><a href="/inventory">Inventory</a></li>
                    <li><a href="/settings">Account Settings</a></li>
                    <li><a href="/logout/">Logout</a></li>
                  </ul>
                </nav>
              </header>
          }
        </div>
        <div className="center-page">
          <div className="center-top-bar">
          </div>
          <CurvedEdge className="top-bar-edge-left" />
          <CurvedEdge className="top-bar-edge-right" />
          <Routes>
            {/* private pages */}
            <Route path="home" element={home} />
            <Route path="sous-chef" element={souschef} />
            <Route path="nutritionist" element={nutritionist} />
            <Route path="recipes" element={recipes} />
            <Route path="inventory" element={inventory} />
            <Route path="settings" element={settings} />
            <Route path="history" element={history} />

            {/* public pages */}
            <Route path="login" element={<Login />} />
            <Route path="create-account" element={<CreateAccount />} />
            <Route path="logout" element={<LogoutPage />} />
            <Route path="/" element={<Login />} />
          </ Routes>
        </div>
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
