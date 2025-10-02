import React from 'react';
import { Box, Alert, IconButton, Slide } from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useApp } from '../../context/AppContext';

const NotificationContainer = () => {
  const { notifications, removeNotification } = useApp();

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 50,
        right: 20,
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
        maxWidth: 400,
        pointerEvents: 'none',
      }}
    >
      <AnimatePresence>
        {notifications.map((notification) => (
          <motion.div
            key={notification.id}
            initial={{ opacity: 0, x: 100, scale: 0.8 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 100, scale: 0.8 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            style={{ pointerEvents: 'auto' }}
          >
            <Alert
              severity={notification.type}
              action={
                <IconButton
                  aria-label="close"
                  color="inherit"
                  size="small"
                  onClick={() => removeNotification(notification.id)}
                  sx={{
                    color: 'inherit',
                    opacity: 0.7,
                    '&:hover': {
                      opacity: 1,
                    },
                  }}
                >
                  <CloseIcon fontSize="small" />
                </IconButton>
              }
              sx={{
                backgroundColor: 'rgba(33, 38, 45, 0.95)',
                backdropFilter: 'blur(16px)',
                border: '1px solid #30363d',
                color: '#f0f6fc',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
                '& .MuiAlert-icon': {
                  color: notification.type === 'success' ? '#238636' :
                         notification.type === 'warning' ? '#d29922' :
                         notification.type === 'error' ? '#f85149' : '#58a6ff',
                },
                '& .MuiAlert-message': {
                  fontSize: '0.875rem',
                  fontWeight: 500,
                },
              }}
            >
              {notification.message}
            </Alert>
          </motion.div>
        ))}
      </AnimatePresence>
    </Box>
  );
};

export default NotificationContainer;