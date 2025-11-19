import React, { useState, useEffect, useRef } from 'react';
import {
    Box,
    TextField,
    IconButton,
    Typography,
    Paper,
    Avatar,
    Chip,
    Menu,
    MenuItem,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    List,
    ListItem,
    ListItemAvatar,
    ListItemText
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import GroupIcon from '@mui/icons-material/Group';
import InfoIcon from '@mui/icons-material/Info';
import { useApp } from '../../context/AppContext';

export default function GroupChatWindow({ group }) {
    const { sendGroupMessage, contacts, currentUser } = useApp();
    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState([]);
    const [anchorEl, setAnchorEl] = useState(null);
    const [membersDialogOpen, setMembersDialogOpen] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Get contact info for a member
    const getMemberInfo = (memberId) => {
        if (memberId === currentUser?.user_id) {
            return { username: 'You', user_id: memberId };
        }
        const contact = contacts?.find(c => c.user_id === memberId);
        return contact || { username: 'Unknown', user_id: memberId };
    };

    const handleSend = async () => {
        if (!message.trim()) return;

        const tempMessage = {
            id: Date.now(),
            message: message,
            sender_id: currentUser.user_id,
            sender_username: 'You',
            timestamp: new Date().toISOString(),
            pending: true
        };

        setMessages(prev => [...prev, tempMessage]);
        const messageToSend = message;
        setMessage('');

        try {
            await sendGroupMessage(group.group_id, messageToSend);
            // Update the temp message to mark it as sent
            setMessages(prev =>
                prev.map(msg =>
                    msg.id === tempMessage.id ? { ...msg, pending: false } : msg
                )
            );
        } catch (error) {
            console.error('Failed to send group message:', error);
            // Mark message as failed
            setMessages(prev =>
                prev.map(msg =>
                    msg.id === tempMessage.id ? { ...msg, failed: true, pending: false } : msg
                )
            );
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleMenuOpen = (event) => {
        setAnchorEl(event.currentTarget);
    };

    const handleMenuClose = () => {
        setAnchorEl(null);
    };

    const handleShowMembers = () => {
        setMembersDialogOpen(true);
        handleMenuClose();
    };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            {/* Header */}
            <Paper
                sx={{
                    p: 2,
                    bgcolor: '#161b22',
                    borderRadius: 0,
                    borderBottom: '1px solid #30363d',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                }}
                elevation={0}
            >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Avatar sx={{ bgcolor: '#238636' }}>
                        <GroupIcon />
                    </Avatar>
                    <Box>
                        <Typography variant="h6" sx={{ color: '#c9d1d9', fontWeight: 600 }}>
                            {group.name}
                        </Typography>
                        <Typography variant="caption" sx={{ color: '#8b949e' }}>
                            {group.members.length} members
                        </Typography>
                    </Box>
                </Box>
                <IconButton onClick={handleMenuOpen} sx={{ color: '#8b949e' }}>
                    <MoreVertIcon />
                </IconButton>
                <Menu
                    anchorEl={anchorEl}
                    open={Boolean(anchorEl)}
                    onClose={handleMenuClose}
                    PaperProps={{
                        sx: { bgcolor: '#161b22', color: '#c9d1d9' }
                    }}
                >
                    <MenuItem onClick={handleShowMembers}>
                        <InfoIcon sx={{ mr: 1, fontSize: 20 }} />
                        View Members
                    </MenuItem>
                </Menu>
            </Paper>

            {/* Messages Area */}
            <Box
                sx={{
                    flex: 1,
                    overflowY: 'auto',
                    p: 2,
                    bgcolor: '#0d1117',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 1
                }}
            >
                {messages.length === 0 ? (
                    <Box
                        sx={{
                            flex: 1,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: '#8b949e'
                        }}
                    >
                        <Typography variant="body2">
                            No messages yet. Start the conversation!
                        </Typography>
                    </Box>
                ) : (
                    messages.map((msg, index) => {
                        const isOwn = msg.sender_id === currentUser?.user_id;
                        return (
                            <Box
                                key={msg.id || index}
                                sx={{
                                    display: 'flex',
                                    justifyContent: isOwn ? 'flex-end' : 'flex-start',
                                    mb: 1
                                }}
                            >
                                <Paper
                                    sx={{
                                        p: 1.5,
                                        maxWidth: '70%',
                                        bgcolor: isOwn ? '#238636' : '#21262d',
                                        color: '#fff',
                                        opacity: msg.pending ? 0.6 : 1,
                                        border: msg.failed ? '1px solid #f85149' : 'none'
                                    }}
                                >
                                    {!isOwn && (
                                        <Typography
                                            variant="caption"
                                            sx={{ color: '#58a6ff', fontWeight: 600, display: 'block', mb: 0.5 }}
                                        >
                                            {msg.sender_username}
                                        </Typography>
                                    )}
                                    <Typography variant="body1" sx={{ wordBreak: 'break-word' }}>
                                        {msg.message}
                                    </Typography>
                                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.6)', mt: 0.5, display: 'block' }}>
                                        {new Date(msg.timestamp).toLocaleTimeString()}
                                        {msg.pending && ' • Sending...'}
                                        {msg.failed && ' • Failed'}
                                    </Typography>
                                </Paper>
                            </Box>
                        );
                    })
                )}
                <div ref={messagesEndRef} />
            </Box>

            {/* Input Area */}
            <Paper
                sx={{
                    p: 2,
                    bgcolor: '#161b22',
                    borderRadius: 0,
                    borderTop: '1px solid #30363d'
                }}
                elevation={0}
            >
                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <TextField
                        fullWidth
                        multiline
                        maxRows={4}
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder={`Message ${group.name}`}
                        variant="outlined"
                        sx={{
                            '& .MuiOutlinedInput-root': {
                                color: '#c9d1d9',
                                bgcolor: '#0d1117',
                                '& fieldset': { borderColor: '#30363d' },
                                '&:hover fieldset': { borderColor: '#58a6ff' },
                                '&.Mui-focused fieldset': { borderColor: '#58a6ff' }
                            },
                            '& .MuiInputBase-input::placeholder': {
                                color: '#8b949e',
                                opacity: 1
                            }
                        }}
                    />
                    <IconButton
                        onClick={handleSend}
                        disabled={!message.trim()}
                        sx={{
                            bgcolor: '#238636',
                            color: '#fff',
                            '&:hover': { bgcolor: '#2ea043' },
                            '&:disabled': { bgcolor: '#21262d', color: '#484f58' }
                        }}
                    >
                        <SendIcon />
                    </IconButton>
                </Box>
            </Paper>

            {/* Members Dialog */}
            <Dialog
                open={membersDialogOpen}
                onClose={() => setMembersDialogOpen(false)}
                maxWidth="sm"
                fullWidth
                PaperProps={{
                    sx: { bgcolor: '#0d1117', color: '#c9d1d9' }
                }}
            >
                <DialogTitle sx={{ bgcolor: '#161b22' }}>
                    Group Members
                </DialogTitle>
                <DialogContent>
                    <List>
                        {group.members.map((memberId) => {
                            const memberInfo = getMemberInfo(memberId);
                            const isAdmin = memberId === group.admin_id;
                            return (
                                <ListItem key={memberId}>
                                    <ListItemAvatar>
                                        <Avatar sx={{ bgcolor: '#238636' }}>
                                            {memberInfo.username[0].toUpperCase()}
                                        </Avatar>
                                    </ListItemAvatar>
                                    <ListItemText
                                        primary={
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Typography sx={{ color: '#c9d1d9' }}>
                                                    {memberInfo.username}
                                                </Typography>
                                                {isAdmin && (
                                                    <Chip
                                                        label="Admin"
                                                        size="small"
                                                        sx={{
                                                            bgcolor: '#238636',
                                                            color: '#fff',
                                                            height: 20,
                                                            fontSize: '0.7rem'
                                                        }}
                                                    />
                                                )}
                                            </Box>
                                        }
                                        secondary={
                                            <Typography variant="caption" sx={{ color: '#8b949e' }}>
                                                {memberId.substring(0, 8)}...
                                            </Typography>
                                        }
                                    />
                                </ListItem>
                            );
                        })}
                    </List>
                </DialogContent>
                <DialogActions sx={{ bgcolor: '#161b22' }}>
                    <Button onClick={() => setMembersDialogOpen(false)} sx={{ color: '#8b949e' }}>
                        Close
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}
