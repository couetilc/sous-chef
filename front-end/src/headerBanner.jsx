import { useNavigate, useLocation } from 'react-router';
import SousChefLogo from './souschef-logo.png';

  //find the url path at which the user is at, so that the navigation banner
  //can be hidden on login pages: "/login" and "/" ("/" redirects to login component)

export default function HeaderBanner() {
  const curLocation = useLocation();

  if ( curLocation.pathname.localeCompare("/") == 0 ||
       curLocation.pathname.localeCompare("/login/") == 0 ||
       curLocation.pathname.localeCompare("/create-account/") == 0 ) {
    return (
      <img src={SousChefLogo} height="300px"/>
    )
  }

  return (
    <header className="header-banner">
      <img src={SousChefLogo} width="150px"/>
      <nav>
        <ul>
          <li><a href="/home">Home</a></li>
          <li><a href="/sous-chef">Sous Chef</a></li>
          <li><a href="/nutritionist">Nutritionist</a></li>
          <li><a href="/recipes">Recipes</a></li>
          <li><a href="/inventory">Inventory</a></li>
          <li><a href="/settings">Account Settings</a></li>
          <li><a href="/logout/">Logout</a></li>
        </ul>
      </nav>
    </header>
  )
}
