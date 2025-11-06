import React, { useState, useEffect } from 'react';
import './style.css';
import SousChefLogo from './souschef-logo.png';
import { useApi } from './useApi';

const PasswordComponent = () => {
    const { api } = useApi();

    const [currentEmail, setCurrentEmail] = useState("");
    const [matching, setMatching] = useState(false);


    useEffect(() => {
        api.getCurrentUser().then((result) => {
            setCurrentEmail(result.email)
        })
    })

    let confirm = ""
    let pass = ""
    function matchPasswords(p, c) {
        pass = p
        confirm = c;
        (confirm === "" || pass !== confirm) ? setMatching(false) : setMatching(true)
    }

    function publishPassword(formData) {
        const password = formData.get('password')

        api.updatePassword({ password })
            .then(() => alert('Password successfully changed!'))
    }

    function publishEmail(formData) {
        const email = formData.get('email')
        api.updateEmail({ email })
            .then((result) => {
                return api.getCurrentUser();
            })
            .then((result) => setCurrentEmail(result.email))
            .then(() => alert('Email successfully changed!'))
    }

    return (
        <>
            <div className="settings-container">
              <form className="email-form" action={publishEmail}>
                <h3>Edit Email</h3>
                <div className="current-email">
                  <p>(current email)</p>
                  <p>{currentEmail}</p>
                </div>
                <input className="text-input-blue" name="email" placeholder="Enter Email" />
                <button className="button-blue" type="submit" name="button">
                  Change Email
                </button>
              </form>
            </div>
            <div className="settings-container">
              <h3>Edit Password</h3>
              <form className="password-form" action={publishPassword}>
                <input className="text-input-blue" name="password" onChange={e=>matchPasswords(e.target.value, confirm)} placeholder="Enter Password" />
                <input className="text-input-blue" name="confirmpassword" onChange={e=>matchPasswords(pass, e.target.value)} placeholder="Confirm Password" />
                <button className="button-blue" type="submit" name="button" disabled={!matching}>Change Password</button>
              </form>
            </div>
        </>
    );
};

export default PasswordComponent;
