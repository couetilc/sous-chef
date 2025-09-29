import './style.css'
import { createRoot } from 'react-dom/client'
import SousChefLogo from './souschef-logo.png'
import { useEffect, useState } from 'react'

export default function App(props) {

  const [health, setHealth] = useState({})

  useEffect(() => {
    fetch('http://localhost:8000/api/health')
      .then(res => res.json())
      .then(json => setHealth(json))
  }, [])

  return (
    <div>
      <img height="200px" src={SousChefLogo} />
      <h1>Hello, World!</h1>
      <p>It's us, <strong>Team 21</strong>, living the dream</p>

      <pre>
        {JSON.stringify(health, null, 2)}
      </pre>
    </div>
  )
}

const root = createRoot(document.getElementById('root'))
root.render(<App />)
