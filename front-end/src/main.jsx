import './style.css'
import { createRoot } from 'react-dom/client'
import { useEffect, useState, useRef } from 'react'

import Login from './login.jsx';
import Home from './home.jsx';
import SousChef from './souschefPage.jsx';
import Nutritionist from './nutritionistPage.jsx';
import Recipes from './recipesPage.jsx';
import Inventory from './inventory.jsx';
import SettingsPage from './settingsPage.jsx';
import CreateAccount from './createAccount.jsx';
import LogoutPage from './logoutPage';
import PrivatePage from './privatePage';
import RecipeHistory from './recipeHistory';
import Layout from './layout.jsx'

import { BrowserRouter, Routes, Route } from "react-router";
import { Link } from 'react-router';
import { StrictMode } from 'react';
import { ApiProvider } from './useApi';
import { UserProvider, useUser } from './useUser';

export default function App(props) {
  const home = <PrivatePage><Home /></PrivatePage>
  const souschef = <PrivatePage><SousChef /></PrivatePage>
  const nutritionist = <PrivatePage><Nutritionist /></PrivatePage>
  const recipes = <PrivatePage><Recipes /></PrivatePage>
  const inventory = <PrivatePage><Inventory /></PrivatePage>
  const settings = <PrivatePage><SettingsPage /></PrivatePage>
  const history = <PrivatePage><RecipeHistory /></PrivatePage>

  return (
    <Layout>
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
      </Routes>
    </Layout>
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
