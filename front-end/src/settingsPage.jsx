import React, { useState } from 'react';
import './style.css';
import SousChefLogo from './souschef-logo.png';
import PasswordComponent from './settingsPassword';
import DeleteComponent from './settingsDeleteAccount';
import DietComponent from './settingsDietPreference';
import Home from './home';

import { BrowserRouter, Routes, Route, Link } from 'react-router';

const SettingsPage = (props) => {
    return (
            <div>
                <div>
                    <h1>
                        <img src={SousChefLogo} width="100" height="100" />
                        Settings
                    </h1>
                    <nav>
                        <Link to="/home">Home</Link>
                    </nav>
                </div>
                <div className="settingsGrid">
                    <PasswordComponent />
                    <DeleteComponent />
                    <DietComponent />
                </div>
            </div>
    );
}

export default SettingsPage;