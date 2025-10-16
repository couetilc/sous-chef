import React, { useState } from 'react';
import { useNavigate } from 'react-router';
import './style.css';
import SousChefLogo from './souschef-logo.png';
import { useApi } from './useApi';


const DeleteComponent = () => {
    const navigate = useNavigate();
    const { api } = useApi();

    function login(formData) {
        const dialog = document.getElementById("deleteAccountDialog")

        const username = formData.get("user");
        const password = formData.get("password");


        api.deleteUser({username, password})
        .then((result) => {
            alert("Successfully deleted account!")
            navigate("/login");
        })
        .catch((error) => {
            alert("Invalid Credentials! Could not delete account!")
            console.log(error)
        })

        dialog.close();
    }

    function showDeleteDialog() {
        const dialog = document.getElementById("deleteAccountDialog")
        dialog.showModal();
    }

    return (
        <div className="delete">
            <dialog id="deleteAccountDialog">
                <form action={login}>
                    <input name="user" placeholder="Enter Username" /> <br />
                    <input name="password" placeholder="Enter Password" /> <br />

                    <button formMethod='dialog'>Cancel</button>
                    <button type='submit'>Submit</button>
                </form>
            </dialog>

            <form action={showDeleteDialog}>
                <button type="submit">Delete Account</button>
            </form>
        </div>
    );
};

export default DeleteComponent;
