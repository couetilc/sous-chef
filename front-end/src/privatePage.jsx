import { useState, useEffect } from 'react';
import { Navigate } from 'react-router';
import { useUser } from './useUser';

export default function PrivatePage(props) {
  const { user, loading } = useUser();

  if (loading) {
    return <div>Authenticating...</div>
  }

  if (!user) {
    return <Navigate to="/login/" />
  }

  return props.children;
}
