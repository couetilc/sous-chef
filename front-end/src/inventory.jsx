import './style.css';
import { useNavigate } from 'react-router';

import SousChefLogo from './souschef-logo.png';

export default function Inventory(props) {
  const navigate = useNavigate();
  let user = props.user;
  let setUser = props.setUser;

  return (
    <div className="centered-div">
      <h1> INVENTORY </h1>
      <p> Welcome to the Inventory Interface page!</p>
      <p> This is still under development, please come back later!</p>
    </div>
  )
}
