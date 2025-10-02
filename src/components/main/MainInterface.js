import React from 'react';
import { Box } from '@mui/material';
import { motion } from 'framer-motion';

// Components
import Sidebar from './Sidebar';
import ChatArea from './ChatArea';
import NotificationContainer from '../ui/NotificationContainer';

const MainInterface = () => {
  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        background: 'linear-gradient(135deg, #0d1117 0%, #161b22 100%)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Background decoration */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `
            radial-gradient(circle at 20% 80%, rgba(35, 134, 54, 0.05) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(88, 166, 255, 0.05) 0%, transparent 50%)
          `,
          pointerEvents: 'none',
        }}
      />

      {/* Sidebar */}
      <motion.div
        initial={{ x: -300, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        style={{ zIndex: 2 }}
      >
        <Sidebar />
      </motion.div>

      {/* Chat Area */}
      <motion.div
        initial={{ x: 100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.5, ease: "easeOut", delay: 0.2 }}
        style={{ flex: 1, zIndex: 1 }}
      >
        <ChatArea />
      </motion.div>

      {/* Notifications */}
      <NotificationContainer />
    </Box>
  );
};

export default MainInterface;