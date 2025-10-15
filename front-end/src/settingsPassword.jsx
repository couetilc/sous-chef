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
        <div className="pass">
            <form action={publishEmail}>
                <p>
                    Current email: {currentEmail}
                </p>
                <p>
                    <input name="email" placeholder="Enter Email" /> <br />
                </p>
                <p>
                    <button type="submit" name="button">Change Email</button>
                </p>
            </form>
            <form action={publishPassword}>
                <p>
                    <input  name="password" onChange={e=>matchPasswords(e.target.value, confirm)} placeholder="Enter Password" /> <br />
                    <input name="confirmpassword" onChange={e=>matchPasswords(pass, e.target.value)} placeholder="Confirm Password" /> <br />
                </p>
                <p>
                    <button type="submit" name="button" disabled={!matching}>Change Password</button>
                </p>
            </form>
        </div>
    );
};

export default PasswordComponent;