import React, { useState } from 'react';
import { 
  Box, 
  List, 
  ListItem, 
  ListItemButton,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Typography,
  IconButton,
  Menu,
  MenuItem,
  Chip,
  Tooltip
} from '@mui/material';
import { 
  MoreVert as MoreIcon,
  Chat as ChatIcon,
  Delete as DeleteIcon,
  Router as RouterIcon,
  Language as WebIcon,
  VpnKey as KeyIcon,
  Schedule as ScheduleIcon,
  PersonAdd as PersonAddIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useApp } from '../../context/AppContext';

const ContactList = () => {
  const { contacts, removeContact, openChat, connectToPeer } = useApp();
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [selectedContact, setSelectedContact] = useState(null);

  const handleMenuOpen = (event, contact) => {
    event.stopPropagation();
    setMenuAnchor(event.currentTarget);
    setSelectedContact(contact);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedContact(null);
  };

  const handleStartChat = () => {
    if (selectedContact) {
      openChat(selectedContact.username);
      handleMenuClose();
    }
  };

  const handleConnect = async () => {
    if (selectedContact) {
      await connectToPeer({
        peer_username: selectedContact.username,
        host: selectedContact.address,
        ws_url: selectedContact.tunnel_url,
      });
      handleMenuClose();
    }
  };

  const handleRemoveContact = async () => {
    if (selectedContact) {
      await removeContact(selectedContact.username);
      handleMenuClose();
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleDateString();
  };

  if (contacts.length === 0) {
    return (
      <Box
        sx={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          p: 3,
        }}
      >
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <PersonAddIcon
            sx={{
              fontSize: 64,
              color: '#30363d',
              mb: 2,
            }}
          />
          <Typography
            variant="h6"
            sx={{
              color: '#8b949e',
              fontWeight: 500,
              mb: 2,
            }}
          >
            No contacts yet
          </Typography>
          <Typography
            variant="body2"
            sx={{
              color: '#6e7681',
              lineHeight: 1.5,
              mb: 3,
            }}
          >
            Add your first contact using the + button to start secure messaging.
          </Typography>
          <Box
            sx={{
              p: 2,
              background: 'rgba(35, 134, 54, 0.1)',
              border: '1px solid rgba(35, 134, 54, 0.3)',
              borderRadius: 2,
              maxWidth: 280,
            }}
          >
            <Typography
              variant="caption"
              sx={{
                color: '#238636',
                fontWeight: 500,
              }}
            >
              💡 Tip: You'll need their public key and connection details
            </Typography>
          </Box>
        </motion.div>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', overflow: 'auto' }}>
      <List sx={{ p: 0 }}>
        {contacts.map((contact, index) => (
          <motion.div
            key={contact.username}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: index * 0.1 }}
          >
            <ListItem
              disablePadding
              sx={{
                borderBottom: '1px solid rgba(48, 54, 61, 0.5)',
              }}
            >
              <ListItemButton
                onClick={() => openChat(contact.username)}
                sx={{
                  py: 2,
                  px: 2,
                  '&:hover': {
                    backgroundColor: 'rgba(48, 54, 61, 0.3)',
                  },
                }}
              >
                <ListItemAvatar>
                  <Avatar
                    sx={{
                      width: 40,
                      height: 40,
                      background: 'linear-gradient(135deg, #30363d 0%, #484f58 100%)',
                      fontSize: '1rem',
                      fontWeight: 600,
                    }}
                  >
                    {contact.username.charAt(0).toUpperCase()}
                  </Avatar>
                </ListItemAvatar>

                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography
                        variant="subtitle2"
                        sx={{
                          color: '#f0f6fc',
                          fontWeight: 600,
                          fontSize: '0.875rem',
                        }}
                      >
                        {contact.username}
                      </Typography>
                      <Tooltip title={`Connection: ${contact.connection_type}`}>
                        {contact.connection_type === 'direct' ? (
                          <RouterIcon sx={{ color: '#58a6ff', fontSize: 16 }} />
                        ) : (
                          <WebIcon sx={{ color: '#d29922', fontSize: 16 }} />
                        )}
                      </Tooltip>
                    </Box>
                  }
                  secondary={
                    <Box sx={{ mt: 0.5 }}>
                      <Typography
                        variant="caption"
                        sx={{
                          color: '#8b949e',
                          fontSize: '0.75rem',
                          display: 'block',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {contact.connection_type === 'direct' 
                          ? `IP: ${contact.address || 'Not set'}`
                          : `Tunnel: ${contact.tunnel_url || 'Not set'}`
                        }
                      </Typography>
                      
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                        <Chip
                          size="small"
                          label={contact.connection_type}
                          sx={{
                            height: 16,
                            fontSize: '0.65rem',
                            backgroundColor: contact.connection_type === 'direct' 
                              ? 'rgba(88, 166, 255, 0.2)' 
                              : 'rgba(210, 153, 34, 0.2)',
                            color: contact.connection_type === 'direct' ? '#58a6ff' : '#d29922',
                            border: `1px solid ${contact.connection_type === 'direct' ? '#58a6ff' : '#d29922'}`,
                          }}
                        />
                        
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <ScheduleIcon sx={{ color: '#6e7681', fontSize: 10 }} />
                          <Typography
                            variant="caption"
                            sx={{
                              color: '#6e7681',
                              fontSize: '0.65rem',
                            }}
                          >
                            Added {formatDate(contact.added_at)}
                          </Typography>
                        </Box>
                      </Box>
                    </Box>
                  }
                />

                <IconButton
                  onClick={(e) => handleMenuOpen(e, contact)}
                  size="small"
                  sx={{
                    color: '#8b949e',
                    '&:hover': {
                      color: '#f0f6fc',
                      backgroundColor: 'rgba(139, 148, 158, 0.1)',
                    },
                  }}
                >
                  <MoreIcon fontSize="small" />
                </IconButton>
              </ListItemButton>
            </ListItem>
          </motion.div>
        ))}
      </List>

      {/* Context Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: {
            background: 'rgba(33, 38, 45, 0.95)',
            backdropFilter: 'blur(16px)',
            border: '1px solid #30363d',
            borderRadius: 2,
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
          }
        }}
      >
        <MenuItem onClick={handleStartChat} sx={{ color: '#f0f6fc', gap: 1 }}>
          <ChatIcon fontSize="small" />
          Start Chat
        </MenuItem>
        <MenuItem onClick={handleConnect} sx={{ color: '#f0f6fc', gap: 1 }}>
          <RouterIcon fontSize="small" />
          Connect
        </MenuItem>
        <MenuItem 
          onClick={handleRemoveContact} 
          sx={{ 
            color: '#f85149', 
            gap: 1,
            '&:hover': {
              backgroundColor: 'rgba(248, 81, 73, 0.1)',
            }
          }}
        >
          <DeleteIcon fontSize="small" />
          Remove Contact
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default ContactList;