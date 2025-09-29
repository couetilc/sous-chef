import './style.css'
import { createRoot } from 'react-dom/client'
import SousChefLogo from './souschef-logo.png';

export default function App(props) {
  return (
    <div>
      <img height="200px" src={SousChefLogo} />
      <h1>Hello, World!</h1>
      <p>It's us, <strong>Team 21</strong>, living the dream</p>
    </div>
  )
}

const root = createRoot(document.getElementById('root'))
root.render(<App />)
