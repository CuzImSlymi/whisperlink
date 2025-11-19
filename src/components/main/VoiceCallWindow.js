import React, { useState, useEffect } from 'react';
import {
    Box,
    Paper,
    Typography,
    IconButton,
    Avatar,
    Slider,
    Chip
} from '@mui/material';
import {
    CallEnd as CallEndIcon,
    Mic as MicIcon,
    MicOff as MicOffIcon,
    VolumeUp as VolumeUpIcon,
    Person as PersonIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';

export default function VoiceCallWindow({ call, peerUsername, onEndCall }) {
    const [muted, setMuted] = useState(false);
    const [volume, setVolume] = useState(80);
    const [duration, setDuration] = useState(0);
    const [connectionQuality, setConnectionQuality] = useState('good'); // 'good', 'fair', 'poor'

    // Timer for call duration
    useEffect(() => {
        const interval = setInterval(() => {
            setDuration(prev => prev + 1);
        }, 1000);

        return () => clearInterval(interval);
    }, []);

    const formatDuration = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    const getQualityColor = () => {
        switch (connectionQuality) {
            case 'good': return '#238636';
            case 'fair': return '#d29922';
            case 'poor': return '#da3633';
            default: return '#8b949e';
        }
    };

    const handleMuteToggle = () => {
        setMuted(!muted);
        // TODO: Implement actual mute via WebRTC
    };

    const handleVolumeChange = (event, newValue) => {
        setVolume(newValue);
        // TODO: Implement actual volume control
    };

    return (
        <Box
            sx={{
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
                bgcolor: '#0d1117',
                position: 'relative',
                overflow: 'hidden'
            }}
        >
            {/* Background gradient */}
            <Box
                sx={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'radial-gradient(circle at 50% 50%, rgba(88, 166, 255, 0.1) 0%, transparent 70%)',
                    pointerEvents: 'none'
                }}
            />

            {/* Call content */}
            <Box
                sx={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative',
                    zIndex: 1,
                    p: 4
                }}
            >
                {/* Avatar with pulse animation */}
                <motion.div
                    animate={{
                        scale: [1, 1.05, 1],
                    }}
                    transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: "easeInOut"
                    }}
                >
                    <Box
                        sx={{
                            position: 'relative',
                            mb: 3
                        }}
                    >
                        <Avatar
                            sx={{
                                width: 120,
                                height: 120,
                                bgcolor: '#58a6ff',
                                fontSize: '3rem',
                                boxShadow: '0 0 40px rgba(88, 166, 255, 0.4)'
                            }}
                        >
                            {peerUsername ? peerUsername[0].toUpperCase() : <PersonIcon sx={{ fontSize: 60 }} />}
                        </Avatar>

                        {/* Animated ring */}
                        <motion.div
                            style={{
                                position: 'absolute',
                                top: -10,
                                left: -10,
                                right: -10,
                                bottom: -10,
                                border: '3px solid #58a6ff',
                                borderRadius: '50%',
                                opacity: 0.6
                            }}
                            animate={{
                                scale: [1, 1.2, 1],
                                opacity: [0.6, 0, 0.6]
                            }}
                            transition={{
                                duration: 2,
                                repeat: Infinity,
                                ease: "easeOut"
                            }}
                        />
                    </Box>
                </motion.div>

                {/* Peer name */}
                <Typography
                    variant="h4"
                    sx={{
                        color: '#f0f6fc',
                        fontWeight: 600,
                        mb: 1
                    }}
                >
                    {peerUsername || 'Unknown'}
                </Typography>

                {/* Call status */}
                <Typography
                    variant="body1"
                    sx={{
                        color: '#8b949e',
                        mb: 1
                    }}
                >
                    {call?.status === 'ringing' ? 'Calling...' :
                        call?.status === 'connecting' ? 'Connecting...' :
                            'In Call'}
                </Typography>

                {/* Duration */}
                <Typography
                    variant="h6"
                    sx={{
                        color: '#58a6ff',
                        fontWeight: 500,
                        fontFamily: 'monospace',
                        mb: 3
                    }}
                >
                    {formatDuration(duration)}
                </Typography>

                {/* Connection quality */}
                <Chip
                    label={`Connection: ${connectionQuality}`}
                    size="small"
                    sx={{
                        bgcolor: 'rgba(88, 166, 255, 0.1)',
                        color: getQualityColor(),
                        border: `1px solid ${getQualityColor()}`,
                        mb: 4
                    }}
                />

                {/* Volume control */}
                <Paper
                    elevation={0}
                    sx={{
                        bgcolor: '#161b22',
                        p: 3,
                        borderRadius: 2,
                        width: '100%',
                        maxWidth: 400,
                        mb: 3
                    }}
                >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <VolumeUpIcon sx={{ color: '#8b949e' }} />
                        <Slider
                            value={volume}
                            onChange={handleVolumeChange}
                            sx={{
                                color: '#58a6ff',
                                '& .MuiSlider-thumb': {
                                    bgcolor: '#58a6ff'
                                },
                                '& .MuiSlider-track': {
                                    bgcolor: '#58a6ff'
                                },
                                '& .MuiSlider-rail': {
                                    bgcolor: '#30363d'
                                }
                            }}
                        />
                        <Typography sx={{ color: '#8b949e', minWidth: 40, textAlign: 'right' }}>
                            {volume}%
                        </Typography>
                    </Box>
                </Paper>

                {/* Call controls */}
                <Box sx={{ display: 'flex', gap: 3, alignItems: 'center' }}>
                    {/* Mute button */}
                    <IconButton
                        onClick={handleMuteToggle}
                        sx={{
                            width: 64,
                            height: 64,
                            bgcolor: muted ? '#da3633' : '#30363d',
                            color: '#fff',
                            '&:hover': {
                                bgcolor: muted ? '#f85149' : '#484f58'
                            },
                            transition: 'all 0.3s'
                        }}
                    >
                        {muted ? <MicOffIcon sx={{ fontSize: 30 }} /> : <MicIcon sx={{ fontSize: 30 }} />}
                    </IconButton>

                    {/* End call button */}
                    <IconButton
                        onClick={onEndCall}
                        sx={{
                            width: 80,
                            height: 80,
                            bgcolor: '#da3633',
                            color: '#fff',
                            '&:hover': {
                                bgcolor: '#f85149',
                                transform: 'scale(1.05)'
                            },
                            transition: 'all 0.3s',
                            boxShadow: '0 0 20px rgba(218, 54, 51, 0.4)'
                        }}
                    >
                        <CallEndIcon sx={{ fontSize: 36 }} />
                    </IconButton>
                </Box>
            </Box>
        </Box>
    );
}
