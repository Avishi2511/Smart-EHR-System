import { createContext, ReactNode, useState, useContext, useEffect } from "react";

export interface SessionContextType {
  isAuthenticated: boolean;
  login: () => void;
  logout: () => void;
}

export const SessionContext = createContext<SessionContextType>({
  isAuthenticated: false,
  login: () => void 0,
  logout: () => void 0,
});

const SESSION_STORAGE_KEY = 'smart-ehr-session';

const SessionContextProvider = ({ children }: { children: ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

  // Load session state from localStorage on mount
  useEffect(() => {
    const savedSession = localStorage.getItem(SESSION_STORAGE_KEY);
    if (savedSession === 'authenticated') {
      setIsAuthenticated(true);
    }
  }, []);

  const login = () => {
    setIsAuthenticated(true);
    localStorage.setItem(SESSION_STORAGE_KEY, 'authenticated');
  };

  const logout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem(SESSION_STORAGE_KEY);
  };

  return (
    <SessionContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </SessionContext.Provider>
  );
};

export const useSession = () => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within a SessionContextProvider');
  }
  return context;
};

export default SessionContextProvider;
