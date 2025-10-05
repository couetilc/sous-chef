import './style.css';
import { createRoot } from 'react-dom/client';
import SousChefLogo from './souschef-logo.png';
import PasswordComponent from './settingsPassword';
import DeleteComponent from './settingsDeleteAccount';
import DietComponent from './settingsDietPreference';

export default function App(props) {
  return (
    <div className='settingsGrid'>
      <PasswordComponent />
      <DeleteComponent />
      <DietComponent />
    </div>
  );
}

const root = createRoot(document.getElementById('root'))
root.render(<App />)
