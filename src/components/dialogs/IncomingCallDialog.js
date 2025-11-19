import React from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Typography,
    Avatar,
    Box
} from '@mui/material';
import {
    Phone as PhoneIcon,
    PhoneDisabled as PhoneDisabledIcon,
    Person as PersonIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';

export default function IncomingCallDialog({ open, caller, onAccept, onReject }) {
    if (!caller) return null;

    return (
        <Dialog
            open={open}
            maxWidth="xs"
            fullWidth
            PaperProps={{
                sx: {
                    bgcolor: '#0d1117',
                    border: '2px solid #58a6ff',
                    boxShadow: '0 0 30px rgba(88, 166, 255, 0.3)'
                }
            }}
        >
            <DialogTitle sx={{ bgcolor: '#161b22', color: '#c9d1d9', textAlign: 'center', pb: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Incoming Call
                </Typography>
            </DialogTitle>

            <DialogContent sx={{ textAlign: 'center', py: 4 }}>
                <motion.div
                    animate={{
                        scale: [1, 1.1, 1],
                    }}
                    transition={{
                        duration: 1.5,
                        repeat: Infinity,
                        ease: "easeInOut"
                    }}
                >
                    <Avatar
                        sx={{
                            width: 80,
                            height: 80,
                            mx: 'auto',
                            mb: 2,
                            bgcolor: '#58a6ff',
                            fontSize: '2rem'
                        }}
                    >
                        {caller.from_username ? caller.from_username[0].toUpperCase() : <PersonIcon />}
                    </Avatar>
                </motion.div>

                <Typography variant="h6" sx={{ color: '#f0f6fc', mb: 1, fontWeight: 600 }}>
                    {caller.from_username || 'Unknown'}
                </Typography>

                <Box
                    sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 1,
                        color: '#8b949e'
                    }}
                >
                    <motion.div
                        animate={{
                            opacity: [0.5, 1, 0.5],
                        }}
                        transition={{
                            duration: 1.5,
                            repeat: Infinity,
                            ease: "easeInOut"
                        }}
                    >
                        <PhoneIcon sx={{ fontSize: 20 }} />
                    </motion.div>
                    <Typography variant="body2">
                        Voice Call
                    </Typography>
                </Box>
            </DialogContent>

            <DialogActions sx={{ bgcolor: '#161b22', px: 3, py: 2, justifyContent: 'space-evenly' }}>
                <Button
                    onClick={onReject}
                    variant="contained"
                    startIcon={<PhoneDisabledIcon />}
                    sx={{
                        bgcolor: '#da3633',
                        color: '#fff',
                        px: 3,
                        py: 1.5,
                        borderRadius: 2,
                        '&:hover': {
                            bgcolor: '#f85149'
                        }
                    }}
                >
                    Decline
                </Button>

                <Button
                    onClick={onAccept}
                    variant="contained"
                    startIcon={<PhoneIcon />}
                    sx={{
                        bgcolor: '#238636',
                        color: '#fff',
                        px: 3,
                        py: 1.5,
                        borderRadius: 2,
                        '&:hover': {
                            bgcolor: '#2ea043'
                        }
                    }}
                >
                    Accept
                </Button>
            </DialogActions>
        </Dialog>
    );
}
