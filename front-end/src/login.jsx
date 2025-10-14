// /src/login
import home from './home.jsx'
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import './style.css';
import SousChefLogo from './souschef-logo.png';
import { useUser } from './useUser.jsx'

export default function Login(props) {
  let user = props.user;
  let setUser = props.setUser;
  const navigate = useNavigate();
  const { login } = useUser();

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
      await login({ username: userText, password: pwElement.value })
      navigate("/home/");
    } catch (error) {
      alert("Invalid Credentials!");
    }
  }

  const loginDiv = {
    border: '5px solid black',
    backgroundColor: 'goldenrod',
    textAlign: 'center'
  };
  return (
    <div className="centered-div">
      <div style={loginDiv}>
        <h1>Log In</h1>
        <label>Username: <input name="userIn" id="userId" /> </label>
        <br />
        <br />
        <label>Password: <input type="password" name="passIn" id="pwId"/> </label>
        <br />
        <br />
        <div className="inline-div" >
        <button className="button"
                type="button"
                style={{backgroundColor: 'tomato', color: 'white'}}
                onClick={() => navigate("/create-account")}>
          Create Account
        </button>
        <div style={{width: '10px'}}></div>
        <button className="button"
                type="button"
                style={{backgroundColor: 'green', color: 'white'}}
                onClick={checkLogin}>
          Continue
        </button>
        </div>
      </div>
    </div>
  );
}
