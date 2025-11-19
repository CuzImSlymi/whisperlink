import React, { useState } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    TextField,
    FormControl,
    FormLabel,
    FormGroup,
    FormControlLabel,
    Checkbox,
    Box,
    Alert,
    CircularProgress
} from '@mui/material';
import { useApp } from '../../context/AppContext';

export default function CreateGroupDialog({ open, onClose, contacts }) {
    const { createGroup } = useApp();
    const [groupName, setGroupName] = useState('');
    const [description, setDescription] = useState('');
    const [selectedMembers, setSelectedMembers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleMemberToggle = (contactId) => {
        setSelectedMembers(prev =>
            prev.includes(contactId)
                ? prev.filter(id => id !== contactId)
                : [...prev, contactId]
        );
    };

    const handleCreate = async () => {
        if (!groupName.trim()) {
            setError('Group name is required');
            return;
        }

        if (selectedMembers.length === 0) {
            setError('Please select at least one member');
            return;
        }

        setLoading(true);
        setError('');

        try {
            await createGroup(groupName, selectedMembers, description);
            // Reset form
            setGroupName('');
            setDescription('');
            setSelectedMembers([]);
            onClose();
        } catch (err) {
            setError(err.message || 'Failed to create group');
        } finally {
            setLoading(false);
        }
    };

    const handleClose = () => {
        if (!loading) {
            setGroupName('');
            setDescription('');
            setSelectedMembers([]);
            setError('');
            onClose();
        }
    };

    return (
        <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
            <DialogTitle sx={{ bgcolor: '#161b22', color: '#c9d1d9' }}>
                Create New Group
            </DialogTitle>
            <DialogContent sx={{ bgcolor: '#0d1117', pt: 2 }}>
                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}

                <TextField
                    autoFocus
                    margin="dense"
                    label="Group Name"
                    type="text"
                    fullWidth
                    variant="outlined"
                    value={groupName}
                    onChange={(e) => setGroupName(e.target.value)}
                    disabled={loading}
                    sx={{
                        mb: 2,
                        '& .MuiOutlinedInput-root': {
                            color: '#c9d1d9',
                            '& fieldset': { borderColor: '#30363d' },
                            '&:hover fieldset': { borderColor: '#58a6ff' },
                            '&.Mui-focused fieldset': { borderColor: '#58a6ff' }
                        },
                        '& .MuiInputLabel-root': { color: '#8b949e' }
                    }}
                />

                <TextField
                    margin="dense"
                    label="Description (optional)"
                    type="text"
                    fullWidth
                    multiline
                    rows={2}
                    variant="outlined"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    disabled={loading}
                    sx={{
                        mb: 2,
                        '& .MuiOutlinedInput-root': {
                            color: '#c9d1d9',
                            '& fieldset': { borderColor: '#30363d' },
                            '&:hover fieldset': { borderColor: '#58a6ff' },
                            '&.Mui-focused fieldset': { borderColor: '#58a6ff' }
                        },
                        '& .MuiInputLabel-root': { color: '#8b949e' }
                    }}
                />

                <FormControl component="fieldset" disabled={loading} fullWidth>
                    <FormLabel component="legend" sx={{ color: '#8b949e', mb: 1 }}>
                        Select Members
                    </FormLabel>
                    <Box sx={{
                        maxHeight: 300,
                        overflowY: 'auto',
                        border: '1px solid #30363d',
                        borderRadius: 1,
                        p: 1
                    }}>
                        <FormGroup>
                            {contacts && contacts.length > 0 ? (
                                contacts.map((contact) => (
                                    <FormControlLabel
                                        key={contact.user_id}
                                        control={
                                            <Checkbox
                                                checked={selectedMembers.includes(contact.user_id)}
                                                onChange={() => handleMemberToggle(contact.user_id)}
                                                sx={{
                                                    color: '#8b949e',
                                                    '&.Mui-checked': { color: '#238636' }
                                                }}
                                            />
                                        }
                                        label={contact.username}
                                        sx={{ color: '#c9d1d9' }}
                                    />
                                ))
                            ) : (
                                <Box sx={{ color: '#8b949e', p: 2, textAlign: 'center' }}>
                                    No contacts available. Add contacts first to create a group.
                                </Box>
                            )}
                        </FormGroup>
                    </Box>
                </FormControl>

                {selectedMembers.length > 0 && (
                    <Box sx={{ mt: 2, color: '#8b949e', fontSize: '0.875rem' }}>
                        {selectedMembers.length} member{selectedMembers.length !== 1 ? 's' : ''} selected
                    </Box>
                )}
            </DialogContent>
            <DialogActions sx={{ bgcolor: '#161b22', px: 3, py: 2 }}>
                <Button
                    onClick={handleClose}
                    disabled={loading}
                    sx={{ color: '#8b949e' }}
                >
                    Cancel
                </Button>
                <Button
                    onClick={handleCreate}
                    disabled={loading}
                    variant="contained"
                    sx={{
                        bgcolor: '#238636',
                        color: '#fff',
                        '&:hover': { bgcolor: '#2ea043' },
                        '&:disabled': { bgcolor: '#21262d', color: '#484f58' }
                    }}
                >
                    {loading ? <CircularProgress size={24} /> : 'Create Group'}
                </Button>
            </DialogActions>
        </Dialog>
    );
}
