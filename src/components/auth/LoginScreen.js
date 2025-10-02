import React, { useState } from 'react';
import { 
  Box, 
  TextField, 
  Button, 
  Typography, 
  Alert,
  Paper,
  InputAdornment,
  IconButton,
  CircularProgress
} from '@mui/material';
import { 
  Visibility, 
  VisibilityOff, 
  Person as PersonIcon,
  Lock as LockIcon,
  Security as SecurityIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const LoginScreen = () => {
  const navigate = useNavigate();
  const { login, loading, error, clearError } = useAuth();
  
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [formError, setFormError] = useState('');

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    
    // Clear errors when user starts typing
    if (formError) setFormError('');
    if (error) clearError();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!formData.username.trim()) {
      setFormError('Username is required');
      return;
    }
    
    if (!formData.password) {
      setFormError('Password is required');
      return;
    }

    const result = await login(formData.username.trim(), formData.password);
    
    if (result.success) {
      navigate('/');
    }
  };

  const displayError = formError || error;

  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #0d1117 0%, #161b22 50%, #21262d 100%)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Background decoration */}
      <Box
        sx={{
          position: 'absolute',
          top: -100,
          right: -100,
          width: 300,
          height: 300,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(35, 134, 54, 0.1) 0%, transparent 70%)',
          pointerEvents: 'none',
        }}
      />
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        <Paper
          elevation={0}
          sx={{
            padding: 4,
            width: 400,
            background: 'rgba(33, 38, 45, 0.8)',
            backdropFilter: 'blur(16px)',
            border: '1px solid rgba(48, 54, 61, 0.5)',
            borderRadius: 3,
            position: 'relative',
          }}
        >
          {/* Header */}
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <motion.div
              whileHover={{ scale: 1.05 }}
              transition={{ duration: 0.2 }}
            >
              <SecurityIcon
                sx={{
                  fontSize: 48,
                  color: '#238636',
                  mb: 2,
                  filter: 'drop-shadow(0 0 12px rgba(35, 134, 54, 0.4))',
                }}
              />
            </motion.div>
            
            <Typography
              variant="h4"
              sx={{
                fontWeight: 700,
                color: '#f0f6fc',
                mb: 1,
                background: 'linear-gradient(135deg, #f0f6fc 0%, #8b949e 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Welcome Back
            </Typography>
            
            <Typography
              variant="body2"
              sx={{
                color: '#8b949e',
                fontWeight: 400,
              }}
            >
              Sign in to your secure WhisperLink account
            </Typography>
          </Box>

          {/* Error Alert */}
          {displayError && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <Alert 
                severity="error" 
                sx={{ 
                  mb: 3,
                  backgroundColor: 'rgba(248, 81, 73, 0.1)',
                  border: '1px solid rgba(248, 81, 73, 0.3)',
                  color: '#f85149',
                  '& .MuiAlert-icon': {
                    color: '#f85149',
                  },
                }}
              >
                {displayError}
              </Alert>
            </motion.div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              name="username"
              label="Username"
              value={formData.username}
              onChange={handleInputChange}
              disabled={loading}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <PersonIcon sx={{ color: '#8b949e', fontSize: 20 }} />
                  </InputAdornment>
                ),
              }}
              sx={{ mb: 3 }}
            />

            <TextField
              fullWidth
              name="password"
              label="Password"
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={handleInputChange}
              disabled={loading}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LockIcon sx={{ color: '#8b949e', fontSize: 20 }} />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                      size="small"
                      sx={{ color: '#8b949e' }}
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{ mb: 4 }}
            />

            <motion.div
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={loading}
                sx={{
                  py: 1.5,
                  fontSize: '1rem',
                  fontWeight: 600,
                  background: 'linear-gradient(135deg, #238636 0%, #2ea043 100%)',
                  boxShadow: '0 4px 12px rgba(35, 134, 54, 0.3)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #2ea043 0%, #238636 100%)',
                    boxShadow: '0 6px 16px rgba(35, 134, 54, 0.4)',
                  },
                  '&:disabled': {
                    background: '#30363d',
                    color: '#8b949e',
                  },
                }}
              >
                {loading ? (
                  <CircularProgress size={24} sx={{ color: '#8b949e' }} />
                ) : (
                  'Sign In'
                )}
              </Button>
            </motion.div>
          </form>

          {/* Register Link */}
          <Box sx={{ textAlign: 'center', mt: 3 }}>
            <Typography variant="body2" sx={{ color: '#8b949e' }}>
              Don't have an account?{' '}
              <Link
                to="/register"
                style={{
                  color: '#238636',
                  textDecoration: 'none',
                  fontWeight: 500,
                }}
              >
                Create one
              </Link>
            </Typography>
          </Box>
        </Paper>
      </motion.div>
    </Box>
  );
};

export default LoginScreen;