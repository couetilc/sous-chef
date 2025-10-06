import React from 'react';
import { useNavigate } from 'react-router';
import './style.css';

// home page, only accesssed after a user has logged in

export default function Home(props) {
  const navigate = useNavigate();

  let user = props.user;
  let setUser = props.setUser;
  // if user is null, no user is logged in, redirect to the login page
  /*
  if ( user == null ) {
    console.log("null user, redirecting to login page");
    return navigate("/login");
  }
  */
  return (
  <>
   <div>
     <p> HOME PAGE </p>
     <p> Hello {user} ! </p>
     <div className=".home-grid">
       <button className="button"> AI Sous Chef </button>
       <button className="button"> Nutritionist </button>
       <button className="button"> Recipes </button>
       <button className="button"> Inventory </button>
     </div>
   </div>
   </>
  )
}
