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
  Badge,
  Chip,
  Button,
  Divider
} from '@mui/material';
import {
  Circle as CircleIcon,
  Lock as LockIcon,
  Schedule as ScheduleIcon,
  Group as GroupIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useApp } from '../../context/AppContext';
import CreateGroupDialog from '../dialogs/CreateGroupDialog';

const ChatList = () => {
  const { contacts, connections, activeChat, openChat, messages, groups, activeGroup, openGroup } = useApp();
  const [createGroupOpen, setCreateGroupOpen] = useState(false);

  // Get contacts that have chat history or active connections
  const chatContacts = contacts.filter(contact =>
    connections.some(conn => conn.peer_username === contact.username) ||
    messages[contact.username]?.length > 0
  );

  const getConnectionStatus = (username) => {
    const connection = connections.find(conn => conn.peer_username === username);
    return connection ? connection.status : 'offline';
  };

  const getLastMessage = (username) => {
    const contactMessages = messages[username];
    if (!contactMessages || contactMessages.length === 0) return null;
    return contactMessages[contactMessages.length - 1];
  };

  const getLastGroupMessage = (groupId) => {
    const groupMessages = messages[`group_${groupId}`];
    if (!groupMessages || groupMessages.length === 0) return null;
    return groupMessages[groupMessages.length - 1];
  };

  const getUnreadCount = (username) => {
    // This would be implemented with actual unread message tracking
    return 0;
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) return 'now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h`;
    return date.toLocaleDateString();
  };

  const hasChats = chatContacts.length > 0 || groups.length > 0;

  if (!hasChats) {
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
          <Typography
            variant="h6"
            sx={{
              color: '#8b949e',
              fontWeight: 500,
              mb: 2,
            }}
          >
            No conversations yet
          </Typography>
          <Typography
            variant="body2"
            sx={{
              color: '#6e7681',
              lineHeight: 1.5,
            }}
          >
            Add contacts and start secure conversations. Your chats will appear here.
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateGroupOpen(true)}
            sx={{
              mt: 3,
              bgcolor: '#238636',
              '&:hover': { bgcolor: '#2ea043' }
            }}
          >
            Create Group
          </Button>
        </motion.div>
        <CreateGroupDialog
          open={createGroupOpen}
          onClose={() => setCreateGroupOpen(false)}
          contacts={contacts}
        />
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', overflow: 'auto' }}>
      {/* Groups Section */}
      {groups.length > 0 && (
        <>
          <Box sx={{ px: 2, py: 1.5, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: '#8b949e', fontWeight: 600, textTransform: 'uppercase' }}>
              Groups
            </Typography>
            <Button
              size="small"
              startIcon={<AddIcon />}
              onClick={() => setCreateGroupOpen(true)}
              sx={{
                color: '#238636',
                fontSize: '0.7rem',
                minWidth: 'auto',
                px: 1
              }}
            >
              New
            </Button>
          </Box>
          <List sx={{ p: 0 }}>
            {groups.map((group, index) => {
              const lastMessage = getLastGroupMessage(group.group_id);
              const isActive = activeGroup === group.group_id;

              return (
                <motion.div
                  key={group.group_id}
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
                      onClick={() => openGroup(group.group_id)}
                      selected={isActive}
                      sx={{
                        py: 2,
                        px: 2,
                        '&.Mui-selected': {
                          backgroundColor: 'rgba(88, 166, 255, 0.15)',
                          borderLeft: '3px solid #58a6ff',
                          '&:hover': {
                            backgroundColor: 'rgba(88, 166, 255, 0.2)',
                          },
                        },
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
                            background: isActive
                              ? 'linear-gradient(135deg, #58a6ff 0%, #388bfd 100%)'
                              : 'linear-gradient(135deg, #30363d 0%, #484f58 100%)',
                          }}
                        >
                          <GroupIcon />
                        </Avatar>
                      </ListItemAvatar>

                      <ListItemText
                        primary={
                          <Typography
                            variant="subtitle2"
                            sx={{
                              color: '#f0f6fc',
                              fontWeight: 600,
                              fontSize: '0.875rem',
                            }}
                          >
                            {group.name}
                          </Typography>
                        }
                        secondary={
                          <Box sx={{ mt: 0.5 }}>
                            {lastMessage ? (
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
                                {lastMessage.sender}: {lastMessage.text}
                              </Typography>
                            ) : (
                              <Typography
                                variant="caption"
                                sx={{
                                  color: '#6e7681',
                                  fontSize: '0.75rem',
                                  fontStyle: 'italic',
                                }}
                              >
                                No messages yet
                              </Typography>
                            )}

                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                              <Chip
                                size="small"
                                label={`${group.members.length} members`}
                                sx={{
                                  height: 16,
                                  fontSize: '0.65rem',
                                  backgroundColor: 'rgba(88, 166, 255, 0.2)',
                                  color: '#58a6ff',
                                  border: '1px solid #58a6ff',
                                }}
                              />

                              {lastMessage && (
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                  <ScheduleIcon sx={{ color: '#6e7681', fontSize: 10 }} />
                                  <Typography
                                    variant="caption"
                                    sx={{
                                      color: '#6e7681',
                                      fontSize: '0.65rem',
                                    }}
                                  >
                                    {formatTime(lastMessage.timestamp)}
                                  </Typography>
                                </Box>
                              )}
                            </Box>
                          </Box>
                        }
                      />
                    </ListItemButton>
                  </ListItem>
                </motion.div>
              );
            })}
          </List>
          {chatContacts.length > 0 && <Divider sx={{ borderColor: '#30363d', my: 1 }} />}
        </>
      )}

      {/* Direct Chats Section */}
      {chatContacts.length > 0 && (
        <>
          <Box sx={{ px: 2, py: 1.5, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: '#8b949e', fontWeight: 600, textTransform: 'uppercase' }}>
              Direct Messages
            </Typography>
            {groups.length === 0 && (
              <Button
                size="small"
                startIcon={<AddIcon />}
                onClick={() => setCreateGroupOpen(true)}
                sx={{
                  color: '#238636',
                  fontSize: '0.7rem',
                  minWidth: 'auto',
                  px: 1
                }}
              >
                New Group
              </Button>
            )}
          </Box>
          <List sx={{ p: 0 }}>
            {chatContacts.map((contact, index) => {
              const connectionStatus = getConnectionStatus(contact.username);
              const lastMessage = getLastMessage(contact.username);
              const unreadCount = getUnreadCount(contact.username);
              const isActive = activeChat === contact.username;

              return (
                <motion.div
                  key={contact.username}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: (index + groups.length) * 0.1 }}
                >
                  <ListItem
                    disablePadding
                    sx={{
                      borderBottom: '1px solid rgba(48, 54, 61, 0.5)',
                    }}
                  >
                    <ListItemButton
                      onClick={() => openChat(contact.username)}
                      selected={isActive}
                      sx={{
                        py: 2,
                        px: 2,
                        '&.Mui-selected': {
                          backgroundColor: 'rgba(35, 134, 54, 0.15)',
                          borderLeft: '3px solid #238636',
                          '&:hover': {
                            backgroundColor: 'rgba(35, 134, 54, 0.2)',
                          },
                        },
                        '&:hover': {
                          backgroundColor: 'rgba(48, 54, 61, 0.3)',
                        },
                      }}
                    >
                      <ListItemAvatar>
                        <Badge
                          overlap="circular"
                          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                          badgeContent={
                            <CircleIcon
                              sx={{
                                color: connectionStatus === 'connected' ? '#238636' : '#8b949e',
                                fontSize: 12,
                                filter: connectionStatus === 'connected'
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
                              background: isActive
                                ? 'linear-gradient(135deg, #238636 0%, #2ea043 100%)'
                                : 'linear-gradient(135deg, #30363d 0%, #484f58 100%)',
                              fontSize: '1rem',
                              fontWeight: 600,
                            }}
                          >
                            {contact.username.charAt(0).toUpperCase()}
                          </Avatar>
                        </Badge>
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
                            <LockIcon
                              sx={{
                                color: '#238636',
                                fontSize: 14,
                                opacity: 0.8
                              }}
                            />
                          </Box>
                        }
                        secondary={
                          <Box sx={{ mt: 0.5 }}>
                            {lastMessage ? (
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
                                {lastMessage.type === 'sent' ? 'You: ' : ''}
                                {lastMessage.text}
                              </Typography>
                            ) : (
                              <Typography
                                variant="caption"
                                sx={{
                                  color: '#6e7681',
                                  fontSize: '0.75rem',
                                  fontStyle: 'italic',
                                }}
                              >
                                No messages yet
                              </Typography>
                            )}

                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                              <Chip
                                size="small"
                                label={connectionStatus === 'connected' ? 'Online' : 'Offline'}
                                sx={{
                                  height: 16,
                                  fontSize: '0.65rem',
                                  backgroundColor: connectionStatus === 'connected'
                                    ? 'rgba(35, 134, 54, 0.2)'
                                    : 'rgba(139, 148, 158, 0.2)',
                                  color: connectionStatus === 'connected' ? '#238636' : '#8b949e',
                                  border: `1px solid ${connectionStatus === 'connected' ? '#238636' : '#8b949e'}`,
                                }}
                              />

                              {lastMessage && (
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                  <ScheduleIcon sx={{ color: '#6e7681', fontSize: 10 }} />
                                  <Typography
                                    variant="caption"
                                    sx={{
                                      color: '#6e7681',
                                      fontSize: '0.65rem',
                                    }}
                                  >
                                    {formatTime(lastMessage.timestamp)}
                                  </Typography>
                                </Box>
                              )}
                            </Box>
                          </Box>
                        }
                      />

                      {unreadCount > 0 && (
                        <Badge
                          badgeContent={unreadCount}
                          color="primary"
                          sx={{
                            '& .MuiBadge-badge': {
                              backgroundColor: '#238636',
                              color: 'white',
                              fontSize: '0.75rem',
                              height: 20,
                              minWidth: 20,
                            },
                          }}
                        />
                      )}
                    </ListItemButton>
                  </ListItem>
                </motion.div>
              );
            })}
          </List>
        </>
      )}

      <CreateGroupDialog
        open={createGroupOpen}
        onClose={() => setCreateGroupOpen(false)}
        contacts={contacts}
      />
    </Box>
  );
};

export default ChatList;