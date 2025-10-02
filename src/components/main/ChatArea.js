import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { motion } from 'framer-motion';
import { 
  Chat as ChatIcon,
  Security as SecurityIcon,
  Shield as ShieldIcon
} from '@mui/icons-material';
import { useApp } from '../../context/AppContext';

// Sub-components
import ChatWindow from './ChatWindow';

const EmptyState = () => (
  <Box
    sx={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      textAlign: 'center',
      p: 4,
    }}
  >
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <Box
        sx={{
          position: 'relative',
          mb: 3,
        }}
      >
        <motion.div
          animate={{ 
            rotate: [0, 5, -5, 0],
            scale: [1, 1.05, 1, 1.05, 1]
          }}
          transition={{ 
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          <ChatIcon
            sx={{
              fontSize: 80,
              color: '#30363d',
              filter: 'drop-shadow(0 0 20px rgba(48, 54, 61, 0.3))',
            }}
          />
        </motion.div>
        
        {/* Security badges */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.5, type: "spring", stiffness: 200 }}
          style={{
            position: 'absolute',
            top: -10,
            right: -10,
          }}
        >
          <SecurityIcon
            sx={{
              fontSize: 24,
              color: '#238636',
              filter: 'drop-shadow(0 0 8px rgba(35, 134, 54, 0.4))',
            }}
          />
        </motion.div>
        
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.7, type: "spring", stiffness: 200 }}
          style={{
            position: 'absolute',
            bottom: -10,
            left: -10,
          }}
        >
          <ShieldIcon
            sx={{
              fontSize: 20,
              color: '#58a6ff',
              filter: 'drop-shadow(0 0 6px rgba(88, 166, 255, 0.4))',
            }}
          />
        </motion.div>
      </Box>

      <Typography
        variant="h5"
        sx={{
          color: '#f0f6fc',
          fontWeight: 600,
          mb: 2,
          background: 'linear-gradient(135deg, #f0f6fc 0%, #8b949e 100%)',
          backgroundClip: 'text',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}
      >
        Welcome to WhisperLink
      </Typography>

      <Typography
        variant="body1"
        sx={{
          color: '#8b949e',
          lineHeight: 1.6,
          maxWidth: 400,
          mb: 3,
        }}
      >
        Select a contact from the sidebar to start a secure, encrypted conversation. 
        Your messages are protected with end-to-end encryption.
      </Typography>

      <Paper
        elevation={0}
        sx={{
          p: 2,
          background: 'rgba(35, 134, 54, 0.1)',
          border: '1px solid rgba(35, 134, 54, 0.3)',
          borderRadius: 2,
          maxWidth: 350,
        }}
      >
        <Typography
          variant="body2"
          sx={{
            color: '#238636',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: 1,
          }}
        >
          <SecurityIcon fontSize="small" />
          End-to-End Encrypted
        </Typography>
        <Typography
          variant="caption"
          sx={{
            color: '#8b949e',
            mt: 0.5,
            display: 'block',
          }}
        >
          Your conversations are private and secure
        </Typography>
      </Paper>
    </motion.div>
  </Box>
);

const ChatArea = () => {
  const { activeChat } = useApp();

  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: 'rgba(13, 17, 23, 0.5)',
        position: 'relative',
      }}
    >
      {activeChat ? (
        <ChatWindow chatUsername={activeChat} />
      ) : (
        <EmptyState />
      )}
    </Box>
  );
};

export default ChatArea;