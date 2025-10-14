import './style.css';
import {useNavigate} from 'react-router';

import SousChefLogo from './souschef-logo.png';

export default function Nutritionist(props) {
  const navigate = useNavigate();
  let user = props.user;
  let setUser = props.setUser;

  return (
    <div className="centered-div">
      <h1> NUTRITION </h1>
      <p> Welcome to the Nutritionist Interface page!</p>
      <p> This is still under development, please come back later!</p>
    </div>
  )
}
