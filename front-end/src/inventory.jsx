import './style.css';
import { useNavigate } from 'react-router';

import SousChefLogo from './souschef-logo.png';

export default function Inventory() {
  const navigate = useNavigate();

  return (
    <div className="centered-div">
      <p> Welcome to the Inventory Interface page!</p>
      <p> This is still under development, please come back later!</p>
    </div>
  )
}
