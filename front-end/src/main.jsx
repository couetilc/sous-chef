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

import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import { Link } from 'react-router';
import { useNavigate, useLocation } from 'react-router';
import { StrictMode } from 'react';
import { ApiProvider } from './useApi';


export default function App(props) {
  const navigate = useNavigate();

  const [curUser, setUser] = useState(null);

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

  //find the url path at which the user is at, so that the navigation banner
  //can be hidden on login pages: "/login" and "/" ("/" redirects to login component)
  const curLocation = useLocation();

  function HeaderBanner() {

    if ( curLocation.pathname.localeCompare("/") == 0 ||
         curLocation.pathname.localeCompare("/login") == 0 ||
         curLocation.pathname.localeCompare("/create-account") == 0 ) {
      return (
        <img src={SousChefLogo} height="300px"/>
      )
    }
    return (
      <header className="header-banner">
        <img src={SousChefLogo} width="150px"/>
        <nav>
          <ul>
            <li><a href="/home">Home</a></li>
            <li><a href="/sous-chef">Sous Chef</a></li>
            <li><a href="/nutritionist">Nutritionist</a></li>
            <li><a href="/recipes">Recipes</a></li>
            <li><a href="/inventory">Inventory</a></li>
            <li><a href="/settings">Account Settings</a></li>
          </ul>
        </nav>
      </header>
    )
  }


  return (
    <>
      <div className="app-container">
        <HeaderBanner />
        <Routes>
          <Route path="login" element={<Login user={curUser} setUser={setUser}/>} />
          <Route path="create-account" element={<CreateAccount user={curUser} setUser={setUser}/>} />
          <Route path="home" element={<Home user={curUser} setUser={setUser}/>} />
          <Route path="sous-chef" element={<SousChef user={curUser} setUser={setUser}/>} />
          <Route path="nutritionist" element={<Nutritionist user={curUser} setUser={setUser}/>} />
          <Route path="recipes" element={<Recipes user={curUser} setUser={setUser}/>} />
          <Route path="inventory" element={<Inventory user={curUser} setUser={setUser} />} />
          <Route path="settings" element={<SettingsPage user={curUser} setUser={setUser} />} />
          // check if user is already logged in
          <Route path="/" element={<Login user={curUser} setUser={setUser}/>} />
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
    <App />
  </ApiProvider>
  </BrowserRouter>
  </StrictMode>
)
