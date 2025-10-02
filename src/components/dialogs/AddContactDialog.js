import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  Alert,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  InputAdornment,
  CircularProgress
} from '@mui/material';
import {
  Person as PersonIcon,
  VpnKey as KeyIcon,
  Language as WebIcon,
  Router as RouterIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useApp } from '../../context/AppContext';

const AddContactDialog = ({ open, onClose }) => {
  const { addContact } = useApp();
  
  const [formData, setFormData] = useState({
    username: '',
    public_key: '',
    connection_type: 'direct',
    address: '',
    tunnel_url: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!formData.username.trim()) {
      setError('Username is required');
      return;
    }
    
    if (!formData.public_key.trim()) {
      setError('Public key is required');
      return;
    }
    
    if (formData.connection_type === 'direct' && !formData.address.trim()) {
      setError('IP address is required for direct connections');
      return;
    }
    
    if (formData.connection_type === 'tunnel' && !formData.tunnel_url.trim()) {
      setError('Tunnel URL is required for tunnel connections');
      return;
    }
    
    setLoading(true);
    
    try {
      const result = await addContact({
        username: formData.username.trim(),
        public_key: formData.public_key.trim(),
        connection_type: formData.connection_type,
        address: formData.connection_type === 'direct' ? formData.address.trim() : null,
        tunnel_url: formData.connection_type === 'tunnel' ? formData.tunnel_url.trim() : null
      });
      
      if (result.success) {
        handleClose();
      } else {
        setError(result.error || 'Failed to add contact');
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({
      username: '',
      public_key: '',
      connection_type: 'direct',
      address: '',
      tunnel_url: ''
    });
    setError('');
    setLoading(false);
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          background: 'rgba(33, 38, 45, 0.95)',
          backdropFilter: 'blur(16px)',
          border: '1px solid #30363d',
          borderRadius: 3,
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5)',
        }
      }}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        <DialogTitle
          sx={{
            color: '#f0f6fc',
            fontWeight: 600,
            fontSize: '1.25rem',
            borderBottom: '1px solid #30363d',
            pb: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >
          Add New Contact
          <Button
            onClick={handleClose}
            size="small"
            sx={{ 
              minWidth: 'auto', 
              color: '#8b949e',
              '&:hover': { color: '#f0f6fc' }
            }}
          >
            <CloseIcon />
          </Button>
        </DialogTitle>

        <form onSubmit={handleSubmit}>
          <DialogContent sx={{ pt: 3 }}>
            {error && (
              <Alert 
                severity="error" 
                sx={{ 
                  mb: 3,
                  backgroundColor: 'rgba(248, 81, 73, 0.1)',
                  border: '1px solid rgba(248, 81, 73, 0.3)',
                  color: '#f85149'
                }}
              >
                {error}
              </Alert>
            )}

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
              name="public_key"
              label="Public Key"
              value={formData.public_key}
              onChange={handleInputChange}
              disabled={loading}
              multiline
              rows={3}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start" sx={{ alignSelf: 'flex-start', mt: 1 }}>
                    <KeyIcon sx={{ color: '#8b949e', fontSize: 20 }} />
                  </InputAdornment>
                ),
              }}
              helperText="Paste the contact's public key here"
              sx={{ mb: 3 }}
            />

            <FormControl component="fieldset" sx={{ mb: 3 }}>
              <FormLabel 
                component="legend" 
                sx={{ 
                  color: '#f0f6fc', 
                  fontWeight: 500,
                  '&.Mui-focused': { color: '#238636' }
                }}
              >
                Connection Type
              </FormLabel>
              <RadioGroup
                name="connection_type"
                value={formData.connection_type}
                onChange={handleInputChange}
                sx={{ mt: 1 }}
              >
                <FormControlLabel
                  value="direct"
                  control={
                    <Radio 
                      sx={{ 
                        color: '#8b949e',
                        '&.Mui-checked': { color: '#238636' }
                      }} 
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <RouterIcon fontSize="small" sx={{ color: '#8b949e' }} />
                      <Typography sx={{ color: '#f0f6fc' }}>Direct Connection</Typography>
                    </Box>
                  }
                />
                <FormControlLabel
                  value="tunnel"
                  control={
                    <Radio 
                      sx={{ 
                        color: '#8b949e',
                        '&.Mui-checked': { color: '#238636' }
                      }} 
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <WebIcon fontSize="small" sx={{ color: '#8b949e' }} />
                      <Typography sx={{ color: '#f0f6fc' }}>Tunnel Connection</Typography>
                    </Box>
                  }
                />
              </RadioGroup>
            </FormControl>

            {formData.connection_type === 'direct' && (
              <TextField
                fullWidth
                name="address"
                label="IP Address"
                value={formData.address}
                onChange={handleInputChange}
                disabled={loading}
                placeholder="192.168.1.100"
                helperText="Enter the contact's IP address for direct connection"
                sx={{ mb: 2 }}
              />
            )}

            {formData.connection_type === 'tunnel' && (
              <TextField
                fullWidth
                name="tunnel_url"
                label="Tunnel URL"
                value={formData.tunnel_url}
                onChange={handleInputChange}
                disabled={loading}
                placeholder="https://example.loca.lt"
                helperText="Enter the tunnel URL (ngrok, loca.lt, etc.)"
                sx={{ mb: 2 }}
              />
            )}
          </DialogContent>

          <DialogActions sx={{ p: 3, pt: 2, borderTop: '1px solid #30363d' }}>
            <Button
              onClick={handleClose}
              disabled={loading}
              sx={{
                color: '#8b949e',
                '&:hover': {
                  backgroundColor: 'rgba(139, 148, 158, 0.1)',
                  color: '#f0f6fc'
                }
              }}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={loading}
              sx={{
                background: 'linear-gradient(135deg, #238636 0%, #2ea043 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #2ea043 0%, #238636 100%)',
                },
                '&:disabled': {
                  background: '#30363d',
                  color: '#8b949e'
                }
              }}
            >
              {loading ? (
                <CircularProgress size={20} sx={{ color: '#8b949e' }} />
              ) : (
                'Add Contact'
              )}
            </Button>
          </DialogActions>
        </form>
      </motion.div>
    </Dialog>
  );
};

export default AddContactDialog;