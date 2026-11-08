/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { UserData, UserRole, StudentProfileData } from '@opportunity-abroad/shared';
import { api, getAccessToken, setAccessToken } from '../services/api';

export interface AuthContextType {
  user: UserData | null;
  accessToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<{ message: string }>;
  logout: () => Promise<void>;
  verifyEmail: (token: string) => Promise<{ message: string }>;
  forgotPassword: (email: string) => Promise<{ message: string }>;
  resetPassword: (token: string, newPassword: string) => Promise<{ message: string }>;
  updateProfile: (data: Partial<StudentProfileData>) => Promise<void>;
  refreshAuth: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchCurrentUser = useCallback(async () => {
    try {
      const userData = await api.users.getMe();
      setUser(userData);
    } catch {
      setUser(null);
      setAccessToken(null);
    }
  }, []);

  const refreshAuth = useCallback(async () => {
    try {
      const token = await api.auth.refresh();
      if (token) {
        await fetchCurrentUser();
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, [fetchCurrentUser]);

  // Initial boot: attempt cookie refresh once on page load to restore in-memory session
  useEffect(() => {
    refreshAuth();

    const handleExpired = () => {
      setUser(null);
      setAccessToken(null);
    };

    window.addEventListener('auth:expired', handleExpired);
    return () => window.removeEventListener('auth:expired', handleExpired);
  }, [refreshAuth]);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await api.auth.login({ email, password });
      setUser(response.user);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName?: string) => {
    return await api.auth.register({ email, password, full_name: fullName });
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await api.auth.logout();
    } finally {
      setUser(null);
      setAccessToken(null);
      setIsLoading(false);
    }
  };

  const verifyEmail = async (token: string) => {
    return await api.auth.verifyEmail(token);
  };

  const forgotPassword = async (email: string) => {
    return await api.auth.forgotPassword(email);
  };

  const resetPassword = async (token: string, newPassword: string) => {
    return await api.auth.resetPassword({ token, new_password: newPassword });
  };

  const updateProfile = async (data: Partial<StudentProfileData>) => {
    const updatedUser = await api.users.updateMe(data);
    setUser(updatedUser);
  };

  const isAuthenticated = !!user;
  const isAdmin = user?.role === ('admin' as UserRole);

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken: getAccessToken(),
        isLoading,
        isAuthenticated,
        isAdmin,
        login,
        register,
        logout,
        verifyEmail,
        forgotPassword,
        resetPassword,
        updateProfile,
        refreshAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
