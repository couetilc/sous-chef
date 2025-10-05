// /src/login
import home from './home.jsx'
import { useState } from 'react';
import { useNavigate } from 'react-router';
import './style.css';
import SousChefLogo from './souschef-logo.png';

// constants for username and password testing
const userCheck = "user";
const pwCheck = "pw";



function navToCreate() {
  //navigate to Create Account page
  const navigate = useNavigate;
  return navigate("/create-account");
}


export default function Login(props) {
  let user = props.user;
  let setUser = props.setUser;
  const navigate = useNavigate();

  function checkLogin() {
    function navToHome() {
      return navigate("/home");
    }
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
    const pwText = pwElement.value;

    if ( !userCheck.localeCompare(userText) && !pwCheck.localeCompare(pwText) ) {
      alert("login successful!");
      setUser(userText);
      navToHome();
    }
    else {
      alert("login failed, incorrect username-password pair!");
      console.log(userText);
      console.log(pwText);
    }
  }
  const loginDiv = {
    border: '5px solid black',
    backgroundColor: 'goldenrod',
    textAlign: 'center'
  };
  return (
    <div style={loginDiv}>
        <h1>Log In</h1>
        <label>Username: <input name="userIn" id="userId" /> </label>
        <br />
        <br />
        <label>Password: <input type="password" name="passIn" id="pwId"/> </label>
        <br />
        <div className="inline-div" >
        <button className="button"
                type="button"
                style={{backgroundColor: 'tomato', color: 'white'}}
                onClick={navToCreate}>
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
  );
}
