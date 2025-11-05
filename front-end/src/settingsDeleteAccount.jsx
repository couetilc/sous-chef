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
    <>
      <dialog id="deleteAccountDialog" >
        <h3>Confirm Account Deletion</h3>
        <form action={login}>
          <input className="text-input" name="user" placeholder="Enter Username" />
          <input className="text-input" name="password" placeholder="Enter Password" />

          <button className="button" type='submit'>Submit</button>
          <button
            className="button-blue"
            formMethod='dialog'
            onClick={e => {
              e.preventDefault()
              document.getElementById("deleteAccountDialog").close()
            }}
          >Cancel</button>
        </form>
      </dialog>

      <div className="settings-container">
        <h3>Delete Account</h3>
        <form action={showDeleteDialog}>
          <button className="button-yellow" type="submit">Confirm Deletion</button>
        </form>
      </div>
    </>
  );
};

export default DeleteComponent;
