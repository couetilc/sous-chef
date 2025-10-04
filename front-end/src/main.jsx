import "./style.css";
import { createRoot } from "react-dom/client";
import SousChefLogo from "./souschef-logo.png";
import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import Login from "./login.jsx";

export default function App(props) {
  return (
    <BrowserRouter>
      <div>
        <img height="200px" src={SousChefLogo} />
        <h1>Welcome to Sous Chef!</h1>
      </div>
      <Routes>
        <Route path="login" element={<Login />} />
        // check if user is already logged in
        <Route path="/" element={<Navigate to="/login" />} />
      </Routes>
    </BrowserRouter>
  );
}

const root = createRoot(document.getElementById("root"));
root.render(<App />);
