import './style.css'
import { createRoot } from 'react-dom/client'
import { useEffect, useState, useRef } from 'react'

import Login from './login.jsx';
import Home from './home.jsx';
import SousChef from './souschefPage.jsx';
import Nutritionist from './nutritionistPage.jsx';
import Nutrition from './nutritionPage.jsx'
import Recipes from './recipesPage.jsx';
import Inventory from './inventory.jsx';
import SettingsPage from './settingsPage.jsx';
import CreateAccount from './createAccount.jsx';
import WelcomePage from './welcomePage.jsx';
import Onboarding from './onboarding';
import HealthOnboarding from './healthOnboarding.jsx';
import LogoutPage from './logoutPage';
import PrivatePage from './privatePage';
import RecipeHistory from './recipeHistory';
import MealPlanPage from'./mealPlan';
import Theme from './theme';
import Layout from './layout.jsx'
import RecipesDetailPage from './recipesDetailPage.jsx';

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
  const nutrition = <PrivatePage><Nutrition /></PrivatePage>
  const settings = <PrivatePage><SettingsPage /></PrivatePage>
  const welcome = <PrivatePage><WelcomePage /></PrivatePage>
  const onboard = <PrivatePage><Onboarding /></PrivatePage>
  const onboardHealth = <PrivatePage><HealthOnboarding/></PrivatePage>
  const history = <PrivatePage><RecipeHistory /></PrivatePage>
  const theme = <PrivatePage><Theme /></PrivatePage>
  const recipesDetail = <PrivatePage><RecipesDetailPage /></PrivatePage>
  const mealPlan = <PrivatePage><MealPlanPage /></PrivatePage>

  return (
    <Layout>
      <Routes>
        {/* private pages */}
        <Route path="home" element={home} />
        <Route path="sous-chef" element={souschef} />
        <Route path="sous-chef/:id" element={souschef} />
        <Route path="nutritionist" element={nutritionist} />
        <Route path="recipes" element={recipes} />
        <Route path="inventory" element={inventory} />
        <Route path="nutrition" element={nutrition} />
        <Route path="settings" element={settings} />
        <Route path="history" element={history} />
        <Route path="welcome" element={welcome} />
        <Route path="onboarding" element={onboard} />
        <Route path="onboard-health" element={onboardHealth} />
        <Route path="theme" element={theme} />
        <Route path="recipes/:id" element={recipesDetail} />
        <Route path="meal-plan" element={mealPlan} />

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
  <BrowserRouter>
  <ApiProvider>
  <UserProvider>
    <App />
  </UserProvider>
  </ApiProvider>
  </BrowserRouter>
)
