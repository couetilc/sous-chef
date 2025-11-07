// /src/login
import home from './home.jsx'
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import './style.css';
import SousChefLogo from './souschef-logo.png';
import { useUser } from './useUser.jsx'
import { useApi } from './useApi.jsx';

export default function Login(props) {
  let user = props.user;
  let setUser = props.setUser;
  const navigate = useNavigate();
  const { login } = useUser();
  const { api } = useApi();

  async function navAfterLogin() {
    //check if user is onboarded already
    const response = await api.getOnboardingStatus();
    if ( response.onboarded == true || response.skipped == true ) {
      navigate("/home/");
    }
    else {
      navigate("/welcome/");
    }
  }

  async function checkLogin() {
    const userElement = document.getElementById("userId");
    if ( userElement.value == '') {
      alert("Please enter your username!");
      return;
    }
    const userText = userElement.value;

    const pwElement = document.getElementById("pwId");
    if ( pwElement.value =='' ) {
      alert("Please enter your password!");
      return;
    }

    try {
      await login({ username: userText, password: pwElement.value });
      await navAfterLogin();
    }
    catch (error) {
      alert("Invalid Credentials!");
    }
  }

  return (
    <div className="login-page">
      <img className="sous-chef-logo" src={SousChefLogo} width="150px"/>
      <div className="login-box">
        <h1>Log In</h1>
        <div className="username-field">
          <label>Username: </label>
          <input name="userIn" id="userId" />
        </div>
        <div className="password-field">
          <label>Password: </label>
          <input type="password" name="passIn" id="pwId"/>
        </div>
        <div className="submission-btns">
          <button
            className="button-blue create-account-button"
            type="button"
            onClick={() => navigate("/create-account")}
          >
            Create Account
          </button>
          <button
            className="button continue-button"
            type="button"
            onClick={checkLogin}
          >
            Continue
          </button>
        </div>
      </div>
    </div>
  );
}
