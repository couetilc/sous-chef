import React, { useState } from 'react';
import './style.css';
import SousChefLogo from './souschef-logo.png';

const PasswordComponent = () => {
    function publish(formData) {
        const pass = formData.get("password");
        const passrepeat = formData.get("confirmpassword");
        if (pass === "") {
            alert(`Password cannot be empty!`);
        }
        else if (pass !== passrepeat) {
            alert(`'${pass}' and '${passrepeat}' do not match!`);
        }
        else {
            alert("Password Saved!");
        }
    }

    return (
        <div className="pass">
            <form action={publish}>
                <p>
                    <input name="password" placeholder="Enter Password" /> <br />
                    <input name="confirmpassword" placeholder="Confirm Password" /> <br />
                </p>
                <p>
                    <button type="submit" name="button">Change Password</button>
                </p>
            </form>
        </div>
    );
};

export default PasswordComponent;