import './style.css'
import { createRoot } from 'react-dom/client'

export default function App(props) {
  return (
    <div>
      <h1>Hello, World!</h1>
      <p>It's us, <strong>Team 21</strong>, living the dream</p>
    </div>
  )
}

const root = createRoot(document.getElementById('root'))
root.render(<App />)
