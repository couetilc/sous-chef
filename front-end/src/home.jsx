import React from 'react';

// home page, accesssed after a user has logged in

export default function Home(props) {
  let user = props.user;
  let setUser = props.setUser;
  return (
  <>
   <div>
     <p> HOME PAGE </p>
     <p> Hello {user} ! </p>
   </div>
   </>
  )
}
