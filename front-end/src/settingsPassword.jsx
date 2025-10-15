import React, { useState, useEffect } from 'react';
import './style.css';
import SousChefLogo from './souschef-logo.png';
import { useApi } from './useApi';

const PasswordComponent = () => {
    const { api } = useApi();

    const [currentEmail, setCurrentEmail] = useState("");

    useEffect(() => {
        api.getCurrentUser().then((result) => {
            setCurrentEmail(result.email)
        })
    })

    function publishPassword(formData) {

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