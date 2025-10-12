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
  const { user, loading, checkAuthStatus, pingBridge, restartBridge } = useAuth();
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    const init = async () => {
      // Wait for Python bridge to be ready
      let bridgeReady = false;
      let attempts = 0;
      const maxAttempts = 5;
      let restartAttempted = false;
      
      while (!bridgeReady && attempts < maxAttempts) {
        attempts++;
        console.log(`Checking bridge readiness (attempt ${attempts}/${maxAttempts})...`);
        
        await new Promise(resolve => setTimeout(resolve, 1000));
        bridgeReady = await pingBridge();
        
        if (!bridgeReady) {
          // Try restarting the bridge once if it's not responding
          if (!restartAttempted && attempts >= 3) {
            console.log('Bridge not responding, attempting restart...');
            restartAttempted = true;
            const restartSuccess = await restartBridge();
            
            if (restartSuccess) {
              console.log('Bridge restart successful, checking again...');
              await new Promise(resolve => setTimeout(resolve, 2000));
              bridgeReady = await pingBridge();
            }
          } else if (attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 2000));
          }
        }
      }
      
      if (bridgeReady) {
        console.log('Python bridge is ready, checking auth status...');
        try {
          await checkAuthStatus();
        } catch (error) {
          console.error('Failed to check auth status during initialization:', error);
          // Continue initialization even if auth check fails
        }
      } else {
        console.warn('Python bridge not responding after restart attempt, continuing without auth check');
      }
      
      setIsInitialized(true);
    };
    init();
  }, [checkAuthStatus, pingBridge, restartBridge]);

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