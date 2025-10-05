import React, { useState } from 'react';
import './style.css';
import SousChefLogo from './souschef-logo.png';
import PasswordComponent from './settingsPassword';
import DeleteComponent from './settingsDeleteAccount';
import DietComponent from './settingsDietPreference';

const SettingsPage = () => {
    return (
        <div>
            <div>
                <h1>
                    <img src={SousChefLogo} width="100" height="100" />
                    Settings
                </h1>
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