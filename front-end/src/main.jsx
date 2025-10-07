import './style.css'
import { createRoot } from 'react-dom/client'
import { useEffect, useState } from 'react'

import SousChefLogo from './souschef-logo.png';
import Login from './login.jsx';
import Home from './home.jsx';
import SettingsPage from './settingsPage.jsx';
import './main.css';

import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import { Link } from 'react-router';
import { useNavigate } from 'react-router';
import { StrictMode } from 'react';



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
        <div className="centered-div">
          <Routes>
            <Route path="login" element={<Login user={curUser} setUser={setUser}/>} />
            <Route path="home" element={<Home user={curUser} setUser={setUser}/>} />
            <Route path="settings" element={<SettingsPage user={curUser} setUser={setUser}/>} />
            // check if user is already logged in
            <Route path="/" element={<Login user={curUser} setUser={setUser}/>} />
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
    <App />
  </BrowserRouter>
  </StrictMode>
)
