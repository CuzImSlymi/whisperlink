import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  IconButton, 
  Tabs, 
  Tab, 
  Avatar,
  Badge,
  Tooltip,
  Button
} from '@mui/material';
import {
  Chat as ChatIcon,
  Contacts as ContactsIcon,
  Settings as SettingsIcon,
  Add as AddIcon,
  PowerSettingsNew as LogoutIcon,
  Person as PersonIcon,
  Circle as CircleIcon
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';

// Sub-components
import ChatList from './ChatList';
import ContactList from './ContactList';
import SettingsPanel from './SettingsPanel';
import AddContactDialog from '../dialogs/AddContactDialog';

const Sidebar = () => {
  const { user, logout } = useAuth();
  const { sidebarTab, setSidebarTab, connections } = useApp();
  const [addContactOpen, setAddContactOpen] = useState(false);

  const handleTabChange = (event, newValue) => {
    setSidebarTab(newValue);
  };

  const handleLogout = async () => {
    await logout();
  };

  const getConnectionStatus = () => {
    return connections.length > 0 ? 'connected' : 'offline';
  };

  const renderTabContent = () => {
    switch (sidebarTab) {
      case 'chats':
        return <ChatList />;
      case 'contacts':
        return <ContactList />;
      case 'settings':
        return <SettingsPanel />;
      default:
        return <ChatList />;
    }
  };

  return (
    <Box
      sx={{
        width: 320,
        height: '100%',
        background: 'rgba(33, 38, 45, 0.95)',
        backdropFilter: 'blur(16px)',
        borderRight: '1px solid #30363d',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
      }}
    >
      {/* User Header */}
      <Box
        sx={{
          p: 2,
          borderBottom: '1px solid #30363d',
          background: 'rgba(13, 17, 23, 0.5)',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Badge
              overlap="circular"
              anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
              badgeContent={
                <CircleIcon
                  sx={{
                    color: getConnectionStatus() === 'connected' ? '#238636' : '#8b949e',
                    fontSize: 12,
                    filter: getConnectionStatus() === 'connected' 
                      ? 'drop-shadow(0 0 4px rgba(35, 134, 54, 0.6))' 
                      : 'none',
                  }}
                />
              }
            >
              <Avatar
                sx={{
                  width: 40,
                  height: 40,
                  background: 'linear-gradient(135deg, #238636 0%, #2ea043 100%)',
                  fontSize: '1.2rem',
                  fontWeight: 600,
                }}
              >
                {user?.username?.charAt(0).toUpperCase() || <PersonIcon />}
              </Avatar>
            </Badge>
            
            <Box>
              <Typography
                variant="subtitle1"
                sx={{
                  color: '#f0f6fc',
                  fontWeight: 600,
                  lineHeight: 1.2,
                }}
              >
                {user?.username || 'User'}
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  color: getConnectionStatus() === 'connected' ? '#238636' : '#8b949e',
                  fontSize: '0.75rem',
                  fontWeight: 500,
                }}
              >
                {getConnectionStatus() === 'connected' ? 'Online' : 'Offline'}
              </Typography>
            </Box>
          </Box>

          <Tooltip title="Logout">
            <IconButton
              onClick={handleLogout}
              size="small"
              sx={{
                color: '#8b949e',
                '&:hover': {
                  color: '#f85149',
                  backgroundColor: 'rgba(248, 81, 73, 0.1)',
                },
              }}
            >
              <LogoutIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Tab Navigation */}
      <Box
        sx={{
          borderBottom: '1px solid #30363d',
          background: 'rgba(13, 17, 23, 0.3)',
        }}
      >
        <Tabs
          value={sidebarTab}
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{
            minHeight: 48,
            '& .MuiTab-root': {
              minHeight: 48,
              color: '#8b949e',
              fontSize: '0.875rem',
              fontWeight: 500,
              textTransform: 'none',
              '&.Mui-selected': {
                color: '#238636',
              },
            },
            '& .MuiTabs-indicator': {
              backgroundColor: '#238636',
              height: 2,
            },
          }}
        >
          <Tab
            value="chats"
            icon={<ChatIcon fontSize="small" />}
            label="Chats"
            iconPosition="start"
          />
          <Tab
            value="contacts"
            icon={<ContactsIcon fontSize="small" />}
            label="Contacts"
            iconPosition="start"
          />
          <Tab
            value="settings"
            icon={<SettingsIcon fontSize="small" />}
            label="Settings"
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Tab Content */}
      <Box sx={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={sidebarTab}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.2 }}
            style={{ height: '100%' }}
          >
            {renderTabContent()}
          </motion.div>
        </AnimatePresence>
      </Box>

      {/* Add Contact FAB for contacts tab */}
      {sidebarTab === 'contacts' && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.3, type: "spring", stiffness: 200 }}
          style={{
            position: 'absolute',
            bottom: 16,
            right: 16,
            zIndex: 10,
          }}
        >
          <Tooltip title="Add Contact">
            <Button
              onClick={() => setAddContactOpen(true)}
              variant="contained"
              sx={{
                minWidth: 56,
                width: 56,
                height: 56,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #238636 0%, #2ea043 100%)',
                boxShadow: '0 4px 12px rgba(35, 134, 54, 0.4)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #2ea043 0%, #238636 100%)',
                  boxShadow: '0 6px 16px rgba(35, 134, 54, 0.5)',
                  transform: 'scale(1.05)',
                },
                transition: 'all 0.2s ease',
              }}
            >
              <AddIcon />
            </Button>
          </Tooltip>
        </motion.div>
      )}

      {/* Add Contact Dialog */}
      <AddContactDialog
        open={addContactOpen}
        onClose={() => setAddContactOpen(false)}
      />
    </Box>
  );
};

export default Sidebar;