import { useEffect } from 'react';
import { useApi } from './useApi';
import { useNavigate } from 'react-router';
import { useUser } from './useUser';

export default function LogoutPage() {
  const { logout } = useUser();
  const navigate = useNavigate();
  useEffect(() => {
    logout().then(() => {
      navigate('/');
    });
  }, [])
  return (
    <div>Logging you out...</div>
  );
}
