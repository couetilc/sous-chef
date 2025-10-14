import { useState, useEffect } from 'react';
import { Navigate } from 'react-router';
import { useUser } from './useUser';

export default function PrivatePage(props) {
  const { user, getCurrentUser } = useUser();

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCurrentUser()
    .catch(() => /* ignore errors */ undefined)
    .finally(() => setLoading(false))
  }, []);

  if (loading) {
    return <div>Authenticating...</div>
  }

  if (!user) {
    return <Navigate to="/login/" />
  }

  return props.children;
}
