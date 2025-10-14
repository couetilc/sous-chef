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
import HeaderBanner from './headerBanner.jsx';
import LogoutPage from './logoutPage';

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
          <Route path="logout" element={<LogoutPage user={curUser} setUser={setUser} />} />
          // check if user is already logged in
          <Route path="/" element={<Login user={curUser} setUser={setUser} />} />
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
