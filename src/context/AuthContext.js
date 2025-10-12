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

  const executeCommand = useCallback(async (command, args = {}, retries = 3) => {
    if (window.electronAPI) {
      for (let attempt = 1; attempt <= retries; attempt++) {
        try {
          const result = await window.electronAPI.executePythonCommand(command, args);
          return result;
        } catch (error) {
          console.error(`Command execution error (attempt ${attempt}/${retries}):`, error);
          
          // If it's the last attempt, throw the error
          if (attempt === retries) {
            throw new Error(`Failed to execute command after ${retries} attempts: ${error.message}`);
          }
          
          // Wait before retrying (exponential backoff)
          const delay = Math.min(1000 * Math.pow(2, attempt - 1), 5000);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
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
        // Check if user data is included (auto-login after registration)
        if (result.user) {
          setUser(result.user);
          return { success: true, user: result.user };
        } else {
          // Fallback: attempt manual login if auto-login wasn't included
          const loginResult = await executeCommand('login_user', { username, password });
          if (loginResult.success) {
            setUser(loginResult.user);
            return { success: true, user: loginResult.user };
          } else {
            throw new Error(loginResult.error || 'Login failed after registration');
          }
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
      // Use fewer retries for auth check to avoid long delays
      const result = await executeCommand('get_current_user', {}, 2);
      
      if (result && result.success && result.user) {
        setUser(result.user);
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Auth check error:', error);
      // Don't show error to user for auth check failures
      setUser(null);
      setError(null);
    } finally {
      setLoading(false);
    }
  }, [executeCommand]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const pingBridge = useCallback(async () => {
    try {
      const result = await executeCommand('ping', {}, 1);
      return result && result.success;
    } catch (error) {
      console.error('Bridge ping failed:', error);
      return false;
    }
  }, [executeCommand]);

  const restartBridge = useCallback(async () => {
    if (window.electronAPI && window.electronAPI.restartPythonBridge) {
      try {
        console.log('Requesting Python bridge restart...');
        const result = await window.electronAPI.restartPythonBridge();
        console.log('Bridge restart result:', result);
        return result.success;
      } catch (error) {
        console.error('Failed to restart bridge:', error);
        return false;
      }
    }
    return false;
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
    pingBridge,
    restartBridge,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};