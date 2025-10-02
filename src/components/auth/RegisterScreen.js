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
  CircularProgress,
  LinearProgress
} from '@mui/material';
import { 
  Visibility, 
  VisibilityOff, 
  Person as PersonIcon,
  Lock as LockIcon,
  Security as SecurityIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const RegisterScreen = () => {
  const navigate = useNavigate();
  const { register, loading, error, clearError } = useAuth();
  
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formErrors, setFormErrors] = useState({});

  // Password strength calculation
  const calculatePasswordStrength = (password) => {
    let score = 0;
    if (password.length >= 8) score += 25;
    if (password.match(/[a-z]/)) score += 25;
    if (password.match(/[A-Z]/)) score += 25;
    if (password.match(/[0-9!@#$%^&*]/)) score += 25;
    return score;
  };

  const passwordStrength = calculatePasswordStrength(formData.password);
  const getPasswordStrengthColor = () => {
    if (passwordStrength < 50) return '#f85149';
    if (passwordStrength < 75) return '#d29922';
    return '#238636';
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    
    // Clear errors when user starts typing
    if (formErrors[name]) {
      setFormErrors(prev => ({
        ...prev,
        [name]: '',
      }));
    }
    if (error) clearError();
  };

  const validateForm = () => {
    const errors = {};
    
    if (!formData.username.trim()) {
      errors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      errors.username = 'Username must be at least 3 characters';
    }
    
    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    }
    
    if (!formData.confirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    const result = await register(formData.username.trim(), formData.password);
    
    if (result.success) {
      navigate('/');
    }
  };

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
          left: -100,
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
              Join WhisperLink
            </Typography>
            
            <Typography
              variant="body2"
              sx={{
                color: '#8b949e',
                fontWeight: 400,
              }}
            >
              Create your secure messaging account
            </Typography>
          </Box>

          {/* Error Alert */}
          {error && (
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
                {error}
              </Alert>
            </motion.div>
          )}

          {/* Register Form */}
          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              name="username"
              label="Username"
              value={formData.username}
              onChange={handleInputChange}
              disabled={loading}
              error={!!formErrors.username}
              helperText={formErrors.username}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <PersonIcon sx={{ color: '#8b949e', fontSize: 20 }} />
                  </InputAdornment>
                ),
                endAdornment: formData.username.length >= 3 && (
                  <InputAdornment position="end">
                    <CheckIcon sx={{ color: '#238636', fontSize: 20 }} />
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
              error={!!formErrors.password}
              helperText={formErrors.password}
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
              sx={{ mb: 2 }}
            />

            {/* Password Strength Indicator */}
            {formData.password && (
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="caption" sx={{ color: '#8b949e' }}>
                    Password Strength
                  </Typography>
                  <Typography variant="caption" sx={{ color: getPasswordStrengthColor() }}>
                    {passwordStrength < 50 ? 'Weak' : passwordStrength < 75 ? 'Good' : 'Strong'}
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={passwordStrength}
                  sx={{
                    height: 4,
                    borderRadius: 2,
                    backgroundColor: '#30363d',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: getPasswordStrengthColor(),
                      borderRadius: 2,
                    },
                  }}
                />
              </Box>
            )}

            <TextField
              fullWidth
              name="confirmPassword"
              label="Confirm Password"
              type={showConfirmPassword ? 'text' : 'password'}
              value={formData.confirmPassword}
              onChange={handleInputChange}
              disabled={loading}
              error={!!formErrors.confirmPassword}
              helperText={formErrors.confirmPassword}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LockIcon sx={{ color: '#8b949e', fontSize: 20 }} />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    {formData.confirmPassword && (
                      formData.password === formData.confirmPassword ? (
                        <CheckIcon sx={{ color: '#238636', fontSize: 20 }} />
                      ) : (
                        <CancelIcon sx={{ color: '#f85149', fontSize: 20 }} />
                      )
                    )}
                    <IconButton
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      edge="end"
                      size="small"
                      sx={{ color: '#8b949e', ml: 1 }}
                    >
                      {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
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
                  'Create Account'
                )}
              </Button>
            </motion.div>
          </form>

          {/* Login Link */}
          <Box sx={{ textAlign: 'center', mt: 3 }}>
            <Typography variant="body2" sx={{ color: '#8b949e' }}>
              Already have an account?{' '}
              <Link
                to="/login"
                style={{
                  color: '#238636',
                  textDecoration: 'none',
                  fontWeight: 500,
                }}
              >
                Sign in
              </Link>
            </Typography>
          </Box>
        </Paper>
      </motion.div>
    </Box>
  );
};

export default RegisterScreen;