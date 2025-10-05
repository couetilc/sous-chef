import './style.css';
import { createRoot } from 'react-dom/client';
import SousChefLogo from './souschef-logo.png';
import PasswordComponent from './settingsPassword';
import DeleteComponent from './settingsDeleteAccount';
import DietComponent from './settingsDietPreference';
import SettingsPage from './settingsPage';

export default function App(props) {
  return (
    <div>
      <SettingsPage />
    </div>
  );
}

const root = createRoot(document.getElementById('root'))
root.render(<App />)
