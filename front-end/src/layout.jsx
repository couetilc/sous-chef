import { useRef, useEffect, useState } from 'react';
import SousChefLogo from './souschef-logo.png';
import { useLocation } from 'react-router';
import CurvedEdge from './curvedEdge';

let checkMobile = () => window.innerWidth < 600

export default function Layout(props) {
  const [isMobile, setIsMobile] = useState(checkMobile);
  const navList = useRef(null);
  const curLocation = useLocation();

  useEffect(() => {
    let handler = () => setIsMobile(checkMobile);
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, []);

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

  let isPublicPage = (
    curLocation.pathname.match(/^\/$/)
    || curLocation.pathname.match(/^\/login\/?$/)
    || curLocation.pathname.match(/^\/create-account\/?$/)
  )

  let CurrentLayout = isMobile ? MobileLayout : DesktopLayout

  return (
    <CurrentLayout isPublicPage={isPublicPage} navRef={navList}>
      {props.children}
    </CurrentLayout>
  )
}

function Nav(props) {
  return (
    <nav>
      <ul ref={props.navRef}>
        <li><a href="/home/">Home</a></li>
        <li><a href="/sous-chef/">Sous Chef</a></li>
        <li><a href="/nutritionist/">Nutritionist</a></li>
        <li><a href="/recipes/">Recipes</a></li>
        <li><a href="/inventory/">Inventory</a></li>
        <li><a href="/history/">History</a></li>
        <li><a href="/nutrition">Nutrition</a></li>
        <li><a href="/settings/">Account Settings</a></li>
        <li><a href="/logout/">Logout</a></li>
      </ul>
    </nav>
  )
}

function DesktopLayout(props) {
  return (
    <div className="app-container">
      {!props.isPublicPage &&
        <div className="left-menu">
          {/* left menu content */}
          <header className="navigation-menu">
            <a className="nav-link-logo" href="/home">
              <img className="sous-chef-logo" src={SousChefLogo} width="150px"/>
            </a>
            <Nav />
          </header>
        </div>
      }
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

function MobileLayout(props) {
  const [open, setOpen] = useState(false);
  return (
    <div className="app-container">
      <div className="top-menu">
        {!props.isPublicPage &&
          <header className="navigation-menu">
            <div className="hamburger-btn" onClick={
              () => setOpen(state => !state)
            }>
              <span>☰</span>
            </div>
            {open && <Nav />}
          </header>
        }
      </div>
      <div className="mobile-center">
        <div className="center-bar-left" />
        <div className="center-page">
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
    </div>
  )
}
