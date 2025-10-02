import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Switch,
  Button,
  TextField,
  Paper,
  Divider,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction
} from '@mui/material';
import { 
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Security as SecurityIcon,
  Wifi as NetworkIcon,
  Notifications as NotificationIcon,
  Palette as ThemeIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';

const SettingsPanel = () => {
  const { user } = useAuth();
  const { serverStatus, serverPort, setServerPort, startServer } = useApp();
  const [tempPort, setTempPort] = useState(serverPort);
  const [settings, setSettings] = useState({
    notifications: true,
    autoConnect: false,
    darkMode: true,
    encryption: true,
  });

  const handleSettingChange = (setting) => (event) => {
    setSettings(prev => ({
      ...prev,
      [setting]: event.target.checked,
    }));
  };

  const handleStartServer = async () => {
    setServerPort(tempPort);
    await startServer(tempPort);
  };

  const handleStopServer = () => {
    // This would stop the server
    console.log('Stop server');
  };

  return (
    <Box sx={{ height: '100%', overflow: 'auto', p: 2 }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* User Info Section */}
        <Paper
          elevation={0}
          sx={{
            p: 3,
            mb: 3,
            background: 'rgba(13, 17, 23, 0.5)',
            border: '1px solid #30363d',
            borderRadius: 2,
          }}
        >
          <Typography variant="h6" sx={{ color: '#f0f6fc', mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <SecurityIcon fontSize="small" />
            User Information
          </Typography>
          
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" sx={{ color: '#8b949e' }}>Username:</Typography>
              <Typography variant="body2" sx={{ color: '#f0f6fc', fontWeight: 500 }}>{user?.username}</Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" sx={{ color: '#8b949e' }}>User ID:</Typography>
              <Typography variant="body2" sx={{ color: '#f0f6fc', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                {user?.user_id?.slice(0, 8)}...
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" sx={{ color: '#8b949e' }}>Public Key:</Typography>
              <Chip 
                label="View" 
                size="small" 
                sx={{ 
                  backgroundColor: 'rgba(35, 134, 54, 0.2)',
                  color: '#238636',
                  height: 20,
                  fontSize: '0.7rem'
                }} 
              />
            </Box>
          </Box>
        </Paper>

        {/* Server Settings */}
        <Paper
          elevation={0}
          sx={{
            p: 3,
            mb: 3,
            background: 'rgba(13, 17, 23, 0.5)',
            border: '1px solid #30363d',
            borderRadius: 2,
          }}
        >
          <Typography variant="h6" sx={{ color: '#f0f6fc', mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <NetworkIcon fontSize="small" />
            Server Settings
          </Typography>
          
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" sx={{ color: '#8b949e', mb: 1 }}>
              Server Status:
            </Typography>
            <Chip
              label={serverStatus === 'running' ? 'Running' : serverStatus === 'starting' ? 'Starting...' : 'Stopped'}
              color={serverStatus === 'running' ? 'success' : serverStatus === 'starting' ? 'warning' : 'default'}
              sx={{
                backgroundColor: serverStatus === 'running' 
                  ? 'rgba(35, 134, 54, 0.2)' 
                  : serverStatus === 'starting' 
                    ? 'rgba(210, 153, 34, 0.2)'
                    : 'rgba(139, 148, 158, 0.2)',
                color: serverStatus === 'running' ? '#238636' : serverStatus === 'starting' ? '#d29922' : '#8b949e',
              }}
            />
          </Box>

          <Box sx={{ mb: 2 }}>
            <TextField
              label="Server Port"
              type="number"
              value={tempPort}
              onChange={(e) => setTempPort(parseInt(e.target.value) || 9001)}
              size="small"
              sx={{ width: '100%', mb: 2 }}
              inputProps={{ min: 1024, max: 65535 }}
            />
            
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                onClick={handleStartServer}
                disabled={serverStatus === 'running' || serverStatus === 'starting'}
                startIcon={<StartIcon />}
                sx={{
                  background: 'linear-gradient(135deg, #238636 0%, #2ea043 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #2ea043 0%, #238636 100%)',
                  },
                  '&:disabled': {
                    background: '#30363d',
                    color: '#8b949e',
                  },
                }}
              >
                Start Server
              </Button>
              
              <Button
                variant="outlined"
                onClick={handleStopServer}
                disabled={serverStatus !== 'running'}
                startIcon={<StopIcon />}
                sx={{
                  borderColor: '#f85149',
                  color: '#f85149',
                  '&:hover': {
                    borderColor: '#f85149',
                    backgroundColor: 'rgba(248, 81, 73, 0.1)',
                  },
                  '&:disabled': {
                    borderColor: '#30363d',
                    color: '#8b949e',
                  },
                }}
              >
                Stop
              </Button>
            </Box>
          </Box>

          {serverStatus === 'running' && (
            <Alert 
              severity="success" 
              sx={{ 
                backgroundColor: 'rgba(35, 134, 54, 0.1)',
                border: '1px solid rgba(35, 134, 54, 0.3)',
                color: '#238636'
              }}
            >
              Server is running on port {serverPort}
            </Alert>
          )}
        </Paper>

        {/* Application Settings */}
        <Paper
          elevation={0}
          sx={{
            p: 3,
            mb: 3,
            background: 'rgba(13, 17, 23, 0.5)',
            border: '1px solid #30363d',
            borderRadius: 2,
          }}
        >
          <Typography variant="h6" sx={{ color: '#f0f6fc', mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <ThemeIcon fontSize="small" />
            Preferences
          </Typography>
          
          <List dense>
            <ListItem>
              <ListItemText
                primary="Desktop Notifications"
                secondary="Receive notifications for new messages"
                primaryTypographyProps={{ color: '#f0f6fc', fontSize: '0.875rem' }}
                secondaryTypographyProps={{ color: '#8b949e', fontSize: '0.75rem' }}
              />
              <ListItemSecondaryAction>
                <Switch
                  checked={settings.notifications}
                  onChange={handleSettingChange('notifications')}
                  color="primary"
                />
              </ListItemSecondaryAction>
            </ListItem>
            
            <Divider sx={{ backgroundColor: '#30363d', my: 1 }} />
            
            <ListItem>
              <ListItemText
                primary="Auto-connect to contacts"
                secondary="Automatically connect when app starts"
                primaryTypographyProps={{ color: '#f0f6fc', fontSize: '0.875rem' }}
                secondaryTypographyProps={{ color: '#8b949e', fontSize: '0.75rem' }}
              />
              <ListItemSecondaryAction>
                <Switch
                  checked={settings.autoConnect}
                  onChange={handleSettingChange('autoConnect')}
                  color="primary"
                />
              </ListItemSecondaryAction>
            </ListItem>
            
            <Divider sx={{ backgroundColor: '#30363d', my: 1 }} />
            
            <ListItem>
              <ListItemText
                primary="End-to-End Encryption"
                secondary="Always encrypt messages (recommended)"
                primaryTypographyProps={{ color: '#f0f6fc', fontSize: '0.875rem' }}
                secondaryTypographyProps={{ color: '#8b949e', fontSize: '0.75rem' }}
              />
              <ListItemSecondaryAction>
                <Switch
                  checked={settings.encryption}
                  onChange={handleSettingChange('encryption')}
                  color="primary"
                  disabled
                />
              </ListItemSecondaryAction>
            </ListItem>
          </List>
        </Paper>

        {/* About Section */}
        <Paper
          elevation={0}
          sx={{
            p: 3,
            background: 'rgba(13, 17, 23, 0.5)',
            border: '1px solid #30363d',
            borderRadius: 2,
          }}
        >
          <Typography variant="h6" sx={{ color: '#f0f6fc', mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <InfoIcon fontSize="small" />
            About WhisperLink
          </Typography>
          
          <Typography variant="body2" sx={{ color: '#8b949e', lineHeight: 1.6 }}>
            WhisperLink is a serverless, peer-to-peer messenger focused on maximum privacy and encryption. 
            Built to resist surveillance and protect conversations from mass scanning or government backdoors.
          </Typography>
          
          <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Chip label="v1.0.0" size="small" sx={{ backgroundColor: '#30363d', color: '#8b949e' }} />
            <Chip label="Open Source" size="small" sx={{ backgroundColor: '#30363d', color: '#8b949e' }} />
            <Chip label="GPL-3.0" size="small" sx={{ backgroundColor: '#30363d', color: '#8b949e' }} />
          </Box>
        </Paper>
      </motion.div>
    </Box>
  );
};

export default SettingsPanel;