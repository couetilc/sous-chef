import './style.css';
import { useNavigate } from 'react-router';

import SousChefLogo from './souschef-logo.png';

export default function SousChef(props) {
  const navigate = useNavigate();
  let user = props.user;
  let setUser = props.setUser;

  return (
    <div className="centered-div">
      <p> Welcome to the Sous Chef Interface page!</p>
      <p> This is still under development, please come back later!</p>
    </div>
  )
}
