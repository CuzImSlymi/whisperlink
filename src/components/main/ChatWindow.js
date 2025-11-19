import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Typography,
  Paper,
  Avatar,
  Chip
} from '@mui/material';
import {
  Send as SendIcon,
  Lock as LockIcon,
  Circle as CircleIcon,
  Close as CloseIcon,
  Phone as PhoneIcon
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/AuthContext';

const ChatWindow = ({ chatUsername }) => {
  const { user } = useAuth();
  const { messages, sendMessage, closeChat, connections, addNotification, contacts, startVoiceCall } = useApp();
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef(null);

  const chatMessages = messages[chatUsername] || [];
  const isConnected = connections.some(conn => conn.peer_username === chatUsername && conn.status === 'connected');

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();

    if (!inputMessage.trim()) return;

    const messageText = inputMessage.trim();
    setInputMessage(''); // Clear input immediately for better UX

    try {
      const result = await sendMessage(chatUsername, messageText);

      if (!result.success) {
        // If sending failed, restore the message to input
        setInputMessage(messageText);
        console.error('Failed to send message:', result.error);

        // Show error notification if available
        if (typeof addNotification === 'function') {
          addNotification(`Failed to send message: ${result.error}`, 'error');
        }
      }
    } catch (error) {
      // If sending failed, restore the message to input
      setInputMessage(messageText);
      console.error('Error sending message:', error);

      // Show error notification if available
      if (typeof addNotification === 'function') {
        addNotification('Failed to send message', 'error');
      }
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: 'rgba(13, 17, 23, 0.5)',
      }}
    >
      {/* Chat Header */}
      <Box
        sx={{
          p: 2,
          borderBottom: '1px solid #30363d',
          background: 'rgba(33, 38, 45, 0.8)',
          backdropFilter: 'blur(16px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar
            sx={{
              width: 36,
              height: 36,
              background: 'linear-gradient(135deg, #238636 0%, #2ea043 100%)',
              fontSize: '0.9rem',
              fontWeight: 600,
            }}
          >
            {chatUsername.charAt(0).toUpperCase()}
          </Avatar>

          <Box>
            <Typography
              variant="subtitle1"
              sx={{
                color: '#f0f6fc',
                fontWeight: 600,
                lineHeight: 1.2,
              }}
            >
              {chatUsername}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CircleIcon
                sx={{
                  color: isConnected ? '#238636' : '#8b949e',
                  fontSize: 8,
                  filter: isConnected ? 'drop-shadow(0 0 4px rgba(35, 134, 54, 0.6))' : 'none',
                }}
              />
              <Typography
                variant="caption"
                sx={{
                  color: isConnected ? '#238636' : '#8b949e',
                  fontSize: '0.75rem',
                  fontWeight: 500,
                }}
              >
                {isConnected ? 'Online' : 'Offline'}
              </Typography>
              <LockIcon
                sx={{
                  color: '#238636',
                  fontSize: 12,
                  ml: 1
                }}
              />
            </Box>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          {/* Voice call button */}
          {isConnected && (
            <IconButton
              onClick={async () => {
                const contact = contacts?.find(c => c.username === chatUsername);
                if (contact) {
                  await startVoiceCall(contact.user_id);
                }
              }}
              size="small"
              sx={{
                color: '#58a6ff',
                '&:hover': {
                  backgroundColor: 'rgba(88, 166, 255, 0.1)',
                },
              }}
              title="Start voice call"
            >
              <PhoneIcon fontSize="small" />
            </IconButton>
          )}

          <IconButton
            onClick={closeChat}
            size="small"
            sx={{
              color: '#8b949e',
              '&:hover': {
                color: '#f0f6fc',
                backgroundColor: 'rgba(139, 148, 158, 0.1)',
              },
            }}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        </Box>
      </Box>

      {/* Messages Area */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 1,
        }}
      >
        {chatMessages.length === 0 ? (
          <Box
            sx={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
            }}
          >
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <LockIcon
                sx={{
                  fontSize: 48,
                  color: '#238636',
                  mb: 2,
                  filter: 'drop-shadow(0 0 12px rgba(35, 134, 54, 0.4))',
                }}
              />
              <Typography
                variant="h6"
                sx={{
                  color: '#f0f6fc',
                  fontWeight: 600,
                  mb: 1,
                }}
              >
                Secure Chat with {chatUsername}
              </Typography>
              <Typography
                variant="body2"
                sx={{
                  color: '#8b949e',
                  lineHeight: 1.6,
                  maxWidth: 300,
                }}
              >
                This conversation is end-to-end encrypted. Send your first message to start chatting securely.
              </Typography>
            </motion.div>
          </Box>
        ) : (
          <AnimatePresence>
            {chatMessages.map((message, index) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: message.type === 'sent' ? 'flex-end' : 'flex-start',
                    mb: 1,
                  }}
                >
                  <Paper
                    elevation={0}
                    sx={{
                      maxWidth: '70%',
                      p: 1.5,
                      background: message.type === 'sent'
                        ? 'linear-gradient(135deg, #238636 0%, #2ea043 100%)'
                        : 'rgba(33, 38, 45, 0.8)',
                      border: message.type === 'sent' ? 'none' : '1px solid #30363d',
                      borderRadius: 2,
                      borderBottomLeftRadius: message.type === 'sent' ? 2 : 0.5,
                      borderBottomRightRadius: message.type === 'sent' ? 0.5 : 2,
                    }}
                  >
                    <Typography
                      variant="body2"
                      sx={{
                        color: message.type === 'sent' ? '#ffffff' : '#f0f6fc',
                        lineHeight: 1.4,
                        wordBreak: 'break-word',
                      }}
                    >
                      {message.text}
                    </Typography>
                    <Typography
                      variant="caption"
                      sx={{
                        color: message.type === 'sent' ? 'rgba(255, 255, 255, 0.7)' : '#8b949e',
                        fontSize: '0.7rem',
                        display: 'block',
                        textAlign: 'right',
                        mt: 0.5,
                      }}
                    >
                      {formatTime(message.timestamp)}
                    </Typography>
                  </Paper>
                </Box>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Message Input */}
      <Box
        sx={{
          p: 2,
          borderTop: '1px solid #30363d',
          background: 'rgba(33, 38, 45, 0.8)',
          backdropFilter: 'blur(16px)',
        }}
      >
        {!isConnected && (
          <Chip
            label="Not connected - messages may not be delivered"
            size="small"
            sx={{
              mb: 1,
              backgroundColor: 'rgba(210, 153, 34, 0.2)',
              color: '#d29922',
              border: '1px solid #d29922',
            }}
          />
        )}

        <form onSubmit={handleSendMessage}>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'end' }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage(e);
                }
              }}
              placeholder="Type a secure message..."
              variant="outlined"
              size="small"
              autoFocus
              sx={{
                '& .MuiOutlinedInput-root': {
                  backgroundColor: 'rgba(13, 17, 23, 0.5)',
                  color: '#f0f6fc',
                  '& fieldset': {
                    borderColor: '#30363d',
                  },
                  '&:hover fieldset': {
                    borderColor: '#484f58',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: '#238636',
                  },
                  '& input': {
                    color: '#f0f6fc',
                  },
                  '& textarea': {
                    color: '#f0f6fc',
                  },
                },
                '& .MuiInputBase-input::placeholder': {
                  color: '#8b949e',
                  opacity: 1,
                },
              }}
            />
            <IconButton
              type="submit"
              disabled={!inputMessage.trim()}
              sx={{
                color: isConnected ? '#238636' : '#d29922',
                backgroundColor: isConnected ? 'rgba(35, 134, 54, 0.1)' : 'rgba(210, 153, 34, 0.1)',
                '&:hover': {
                  backgroundColor: isConnected ? 'rgba(35, 134, 54, 0.2)' : 'rgba(210, 153, 34, 0.2)',
                },
                '&:disabled': {
                  color: '#6e7681',
                  backgroundColor: 'transparent',
                },
              }}
            >
              <SendIcon />
            </IconButton>
          </Box>
        </form>
      </Box>
    </Box>
  );
};

export default ChatWindow;