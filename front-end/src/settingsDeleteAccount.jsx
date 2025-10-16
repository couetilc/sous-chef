import React, { useState } from 'react';
import './style.css';
import SousChefLogo from './souschef-logo.png';
import { useApi } from './useApi';


const DeleteComponent = () => {
    const { api } = useApi();

    function login(formData) {
        const dialog = document.getElementById("deleteAccountDialog")

        const username = formData.get("user");
        const password = formData.get("password");


        api.deleteUser({username, password})
        .then((result) => {
            console.log(result);
            if (result.id) {
                alert('Successful login: Deleting account...');
            } else {
                alert('Invalid Credentials');
            }
        })
        .catch((error) => console.error(error))

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
