import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { authApi } from "../api/auth";
import { ApiError } from "../api/client";
import type { LoginPayload, RegisterPayload, User } from "../types/user";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // On first load, ask the API who we are. The auth cookie (if any)
    // is sent automatically; if there isn't one or it's expired, this
    // simply resolves to "logged out" rather than throwing visibly.
    authApi
      .me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false));
  }, []);

  async function login(payload: LoginPayload) {
    const loggedInUser = await authApi.login(payload);
    setUser(loggedInUser);
  }

  async function register(payload: RegisterPayload) {
    const newUser = await authApi.register(payload);
    setUser(newUser);
  }

  async function logout() {
    await authApi.logout();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
}

export { ApiError };
