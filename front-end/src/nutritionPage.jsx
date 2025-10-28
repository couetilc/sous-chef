import './style.css';
import {useNavigate} from 'react-router';

import SousChefLogo from './souschef-logo.png';

export default function Nutrition() {
  const navigate = useNavigate();

  return (
    <div className="centered-div">
      <h1> NUTRITION </h1>
      <p> Welcome to the Nutrition Interface page!</p>
      <p> This is still under development, please come back later!</p>
    </div>
  )
}
