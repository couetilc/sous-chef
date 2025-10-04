// /src/Login

// constants for username and password testing
const user = "user";
const pw = "pw";

function checkLogin() {
  const userElement = document.getElementById("userId");
  if (userElement.value == "") {
    alert("Please enter your username!");
    return;
  }
  const userText = userElement.value;

  const pwElement = document.getElementById("pwId");
  if (pwElement.value == "") {
    alert("Please enter your password!");
    return;
  }
  const pwText = pwElement.value;

  if (!user.localeCompare(userText) && !pw.localeCompare(pwText)) {
    alert("login successful!");
  } else {
    alert("login failed, incorrect username-password pair!");
    console.log(userText);
    console.log(pwText);
  }
}

export default function Login() {
  return (
    <div>
      <p>LOGIN PAGE</p>
      <label>
        Username: <input name="userIn" id="userId" />{" "}
      </label>
      <br />
      <br />
      <label>
        Password: <input type="password" name="passIn" id="pwId" />{" "}
      </label>
      <br />
      <button className="login-button" type="button" onClick={checkLogin}>
        Log In
      </button>
    </div>
  );
}
