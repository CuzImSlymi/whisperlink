import React, { createContext, useContext, useState, useCallback } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const executeCommand = useCallback(async (command, args = {}) => {
    if (window.electronAPI) {
      try {
        const result = await window.electronAPI.executePythonCommand(command, args);
        return result;
      } catch (error) {
        console.error('Command execution error:', error);
        throw new Error(`Failed to execute command: ${error.message}`);
      }
    } else {
      // Fallback for web development
      console.warn('Electron API not available, using mock data');
      return { success: true, message: 'Mock response' };
    }
  }, []);

  const register = useCallback(async (username, password) => {
    setLoading(true);
    setError(null);

    try {
      const result = await executeCommand('register_user', { username, password });
      
      if (result.success) {
        // After registration, automatically log in
        const loginResult = await executeCommand('login_user', { username, password });
        if (loginResult.success) {
          setUser(loginResult.user);
          return { success: true, user: loginResult.user };
        } else {
          throw new Error(loginResult.error || 'Login failed after registration');
        }
      } else {
        throw new Error(result.error || 'Registration failed');
      }
    } catch (error) {
      setError(error.message);
      return { success: false, error: error.message };
    } finally {
      setLoading(false);
    }
  }, [executeCommand]);

  const login = useCallback(async (username, password) => {
    setLoading(true);
    setError(null);

    try {
      const result = await executeCommand('login_user', { username, password });
      
      if (result.success) {
        setUser(result.user);
        return { success: true, user: result.user };
      } else {
        throw new Error(result.error || 'Login failed');
      }
    } catch (error) {
      setError(error.message);
      return { success: false, error: error.message };
    } finally {
      setLoading(false);
    }
  }, [executeCommand]);

  const logout = useCallback(async () => {
    setLoading(true);
    
    try {
      await executeCommand('logout_user');
      setUser(null);
      setError(null);
    } catch (error) {
      console.error('Logout error:', error);
      // Even if logout fails, clear local state
      setUser(null);
      setError(null);
    } finally {
      setLoading(false);
    }
  }, [executeCommand]);

  const checkAuthStatus = useCallback(async () => {
    setLoading(true);
    
    try {
      const result = await executeCommand('get_current_user');
      
      if (result.success && result.user) {
        setUser(result.user);
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Auth check error:', error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, [executeCommand]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const value = {
    user,
    loading,
    error,
    register,
    login,
    logout,
    checkAuthStatus,
    clearError,
    executeCommand,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};