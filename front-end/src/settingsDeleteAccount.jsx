import React, { useState } from 'react';
import './style.css';
import SousChefLogo from './souschef-logo.png';


const DeleteComponent = () => {
    function publish(formData) {
        alert("Deleting account");
    }
    return (
        <div className="delete">
            <form action={publish}>
                <button type="submit">Delete Account</button>
            </form>
        </div>
    );
};

export default DeleteComponent;