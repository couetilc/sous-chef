import { useEffect } from 'react';
import { useApi } from './useApi';
import { useNavigate } from 'react-router';

export default function LogoutPage() {
  const api = useApi();
  const navigate = useNavigate();
  useEffect(() => {
    api.logout().then(() => {
      navigate('/');
    });
  }, [])
  return (
    <div>Logging you out...</div>
  );
}
