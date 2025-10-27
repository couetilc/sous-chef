import { useRef, useEffect } from 'react';
import SousChefLogo from './souschef-logo.png';
import { useLocation } from 'react-router';
import CurvedEdge from './curvedEdge';

export default function Layout(props) {
  const curLocation = useLocation();

  const navList = useRef(null);
  useEffect(() => {
    if (navList.current) {
      for (let a of navList.current.querySelectorAll('a')) {
          let trimTrailingSlash = str => str.replace(/\/$/, '')
          if (
            trimTrailingSlash(a.href)
            === trimTrailingSlash(window.location.href)
          ) {
            a.classList.add('active')
          } else {
            a.classList.remove('active')
          }
      }
    }
  }, [navList])

  return (
    <div className="app-container">
      <div className="left-menu">
        {/* left menu content */}
        {( curLocation.pathname.localeCompare("/") == 0 ||
          curLocation.pathname.localeCompare("/login/") == 0 ||
          curLocation.pathname.localeCompare("/create-account/") == 0)
          ? <img className="sous-chef-logo" src={SousChefLogo} height="300px"/>
          : <header className="navigation-menu">
            <div className="hamburger-button" onClick={
              e => getComputedStyle(e.currentTarget)['margin-left'] == '0px'
                ? e.currentTarget.style['margin-left'] = 'calc(100% - 2em)'
                : e.currentTarget.style['margin-left'] = '0'
            }>
              <span>☰</span>
            </div>
            <a className="nav-link-logo" href="/home">
              <img className="sous-chef-logo" src={SousChefLogo} width="150px"/>
            </a>
            <nav>
              <ul ref={navList}>
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
        }
      </div>
      <div className="center-bar-left" />
      <div className="center-page">
        <div className="center-top-bar" />
        <CurvedEdge className="top-bar-edge-left" />
        <CurvedEdge className="top-bar-edge-right" />
        <div className="center-page-middle">
          {props.children}
        </div>
        <CurvedEdge className="bottom-bar-edge-left" />
        <CurvedEdge className="bottom-bar-edge-right" />
        <div className="center-bottom-bar" />
      </div>
      <div className="center-bar-right" />
    </div>
  )
}
