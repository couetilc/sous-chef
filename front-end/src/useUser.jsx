import { createContext, useState, useEffect, useContext, useMemo } from 'react';
import { useApi } from './useApi';

const UserContext = createContext();

export function useUser() {
  return useContext(UserContext);
}

export function UserProvider(props) {
  const { api } = useApi();

  const [user, setUser] = useState();

  const context = useMemo(() => {
    return {
      user,
      async login({ username, password }) {
        const user = await api.login({ username, password })
        setUser(user);
      },
      async logout() {
        await api.logout();
        setUser(undefined);
      },
      async getCurrentUser() {
        const user = await api.getCurrentUser();
        setUser(user);
      },
    }
  }, [user, api]);

  return (
    <UserContext value={context}>
      {props.children}
    </UserContext>
  )
}
