import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
// import { motion, AnimatePresence } from 'framer-motion';

// Components
import LoginScreen from './components/auth/LoginScreen';
import RegisterScreen from './components/auth/RegisterScreen';
import MainInterface from './components/main/MainInterface';
import TitleBar from './components/layout/TitleBar';

// Context
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppProvider } from './context/AppContext';

// Styles
import './App.css';

function AppContent() {
  const { user, loading, checkAuthStatus } = useAuth();
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    const init = async () => {
      await checkAuthStatus();
      setIsInitialized(true);
    };
    init();
  }, []);

  if (!isInitialized || loading) {
    return (
      <Box
        sx={{
          height: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #0d1117 0%, #161b22 100%)',
        }}
      >
        <CircularProgress 
          size={48} 
          thickness={3}
          sx={{ 
            color: '#238636',
            filter: 'drop-shadow(0 0 8px rgba(35, 134, 54, 0.3))'
          }} 
        />
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <TitleBar />
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        <Routes>
            <Route
              path="/login"
              element={
                user ? (
                  <Navigate to="/" replace />
                ) : (
                  <LoginScreen />
                )
              }
            />
            <Route
              path="/register"
              element={
                user ? (
                  <Navigate to="/" replace />
                ) : (
                  <RegisterScreen />
                )
              }
            />
            <Route
              path="/"
              element={
                user ? (
                  <MainInterface />
                ) : (
                  <Navigate to="/login" replace />
                )
              }
            />
          </Routes>
      </Box>
    </Box>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppProvider>
          <AppContent />
        </AppProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;