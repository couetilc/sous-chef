import React, { useState } from 'react';
import './style.css';
import SousChefLogo from './souschef-logo.png';
import PasswordComponent from './settingsPassword';
import DeleteComponent from './settingsDeleteAccount';
import DietComponent from './settingsDietPreference';
import RestrictedIngredientsComponent from './settingsRestrictedIngredients';
import Home from './home';

import { BrowserRouter, Routes, Route, Link } from 'react-router';

const SettingsPage = () => {
    return (
            <div className="settings-page">
                <h1>Settings</h1>
                <div className="settings-sections">
                  <PasswordComponent />
                  <DeleteComponent />
                  <DietComponent />
                  <RestrictedIngredientsComponent />
                </div>
            </div>
    );
}

export default SettingsPage;
