import React from 'react';
import { Box, Typography, IconButton } from '@mui/material';
import { 
  Minimize as MinimizeIcon,
  CropSquare as MaximizeIcon,
  Close as CloseIcon,
  Lock as LockIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';

const TitleBar = () => {
  const handleMinimize = () => {
    if (window.electronAPI) {
      window.electronAPI.minimize();
    }
  };

  const handleMaximize = () => {
    if (window.electronAPI) {
      window.electronAPI.maximize();
    }
  };

  const handleClose = () => {
    if (window.electronAPI) {
      window.electronAPI.close();
    }
  };

  return (
    <Box
      sx={{
        height: 40,
        background: 'linear-gradient(135deg, #0d1117 0%, #21262d 100%)',
        borderBottom: '1px solid #30363d',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 16px',
        WebkitAppRegion: 'drag',
        userSelect: 'none',
        position: 'relative',
        zIndex: 1000,
      }}
    >
      {/* Left side - App title */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <motion.div
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
        >
          <LockIcon 
            sx={{ 
              color: '#238636', 
              fontSize: 20,
              filter: 'drop-shadow(0 0 4px rgba(35, 134, 54, 0.4))'
            }} 
          />
        </motion.div>
        <Typography
          variant="body2"
          sx={{
            fontWeight: 600,
            color: '#f0f6fc',
            fontSize: '0.875rem',
            letterSpacing: '0.5px',
          }}
        >
          WhisperLink
        </Typography>
      </Box>

      {/* Center - Connection status indicator */}
      <Box
        sx={{
          position: 'absolute',
          left: '50%',
          transform: 'translateX(-50%)',
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <motion.div
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        >
          <Box
            sx={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: '#238636',
              boxShadow: '0 0 8px rgba(35, 134, 54, 0.6)',
            }}
          />
        </motion.div>
        <Typography
          variant="caption"
          sx={{
            color: '#8b949e',
            fontSize: '0.75rem',
            fontWeight: 500,
          }}
        >
          Secure
        </Typography>
      </Box>

      {/* Right side - Window controls */}
      <Box 
        sx={{ 
          display: 'flex', 
          alignItems: 'center',
          WebkitAppRegion: 'no-drag',
        }}
      >
        <IconButton
          onClick={handleMinimize}
          size="small"
          sx={{
            color: '#8b949e',
            padding: '4px',
            borderRadius: '4px',
            '&:hover': {
              backgroundColor: 'rgba(139, 148, 158, 0.1)',
              color: '#f0f6fc',
            },
          }}
        >
          <MinimizeIcon fontSize="small" />
        </IconButton>
        
        <IconButton
          onClick={handleMaximize}
          size="small"
          sx={{
            color: '#8b949e',
            padding: '4px',
            borderRadius: '4px',
            '&:hover': {
              backgroundColor: 'rgba(139, 148, 158, 0.1)',
              color: '#f0f6fc',
            },
          }}
        >
          <MaximizeIcon fontSize="small" />
        </IconButton>
        
        <IconButton
          onClick={handleClose}
          size="small"
          sx={{
            color: '#8b949e',
            padding: '4px',
            borderRadius: '4px',
            '&:hover': {
              backgroundColor: 'rgba(248, 81, 73, 0.2)',
              color: '#f85149',
            },
          }}
        >
          <CloseIcon fontSize="small" />
        </IconButton>
      </Box>
    </Box>
  );
};

export default TitleBar;