import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';

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
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <CircularProgress 
            size={48} 
            thickness={3}
            sx={{ 
              color: '#238636',
              filter: 'drop-shadow(0 0 8px rgba(35, 134, 54, 0.3))'
            }} 
          />
        </motion.div>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <TitleBar />
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        <AnimatePresence mode="wait">
          <Routes>
            <Route
              path="/login"
              element={
                user ? (
                  <Navigate to="/" replace />
                ) : (
                  <motion.div
                    key="login"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ duration: 0.3 }}
                  >
                    <LoginScreen />
                  </motion.div>
                )
              }
            />
            <Route
              path="/register"
              element={
                user ? (
                  <Navigate to="/" replace />
                ) : (
                  <motion.div
                    key="register"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ duration: 0.3 }}
                  >
                    <RegisterScreen />
                  </motion.div>
                )
              }
            />
            <Route
              path="/"
              element={
                user ? (
                  <motion.div
                    key="main"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 1.05 }}
                    transition={{ duration: 0.3 }}
                  >
                    <MainInterface />
                  </motion.div>
                ) : (
                  <Navigate to="/login" replace />
                )
              }
            />
          </Routes>
        </AnimatePresence>
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