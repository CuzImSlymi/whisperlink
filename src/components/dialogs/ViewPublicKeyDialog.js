import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Box,
  IconButton,
  Alert,
  Chip
} from '@mui/material';
import {
  Close as CloseIcon,
  ContentCopy as CopyIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon
} from '@mui/icons-material';

const ViewPublicKeyDialog = ({ open, onClose, user }) => {
  const [copied, setCopied] = useState(false);
  const [showFullKey, setShowFullKey] = useState(false);

  const handleCopyKey = async () => {
    if (user?.public_key) {
      try {
        await navigator.clipboard.writeText(user.public_key);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (error) {
        console.error('Failed to copy to clipboard:', error);
      }
    }
  };

  const formatPublicKey = (key) => {
    if (!key) return '';
    if (showFullKey) return key;
    return `${key.slice(0, 32)}...${key.slice(-32)}`;
  };

  const handleClose = () => {
    setShowFullKey(false);
    setCopied(false);
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          background: 'rgba(13, 17, 23, 0.95)',
          border: '1px solid #30363d',
          borderRadius: 2,
          backdropFilter: 'blur(20px)',
        }
      }}
    >
      <DialogTitle
        sx={{
          color: '#f0f6fc',
          borderBottom: '1px solid #30363d',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="h6">Public Key Information</Typography>
        </Box>
        <IconButton onClick={handleClose} sx={{ color: '#8b949e' }}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ p: 3 }}>
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" sx={{ color: '#8b949e', mb: 1 }}>
            Username:
          </Typography>
          <Typography variant="body1" sx={{ color: '#f0f6fc', fontWeight: 500 }}>
            {user?.username}
          </Typography>
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" sx={{ color: '#8b949e', mb: 1 }}>
            User ID:
          </Typography>
          <Typography variant="body1" sx={{ color: '#f0f6fc', fontFamily: 'monospace' }}>
            {user?.user_id}
          </Typography>
        </Box>

        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" sx={{ color: '#8b949e' }}>
              Public Key:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Chip
                label={showFullKey ? "Hide" : "Show Full"}
                size="small"
                onClick={() => setShowFullKey(!showFullKey)}
                icon={showFullKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                sx={{
                  backgroundColor: 'rgba(88, 166, 255, 0.2)',
                  color: '#58a6ff',
                  cursor: 'pointer',
                  '&:hover': {
                    backgroundColor: 'rgba(88, 166, 255, 0.3)',
                  }
                }}
              />
            </Box>
          </Box>
          
          <TextField
            fullWidth
            multiline
            rows={showFullKey ? 8 : 2}
            value={formatPublicKey(user?.public_key)}
            InputProps={{
              readOnly: true,
              endAdornment: (
                <IconButton
                  onClick={handleCopyKey}
                  sx={{ color: '#8b949e' }}
                  size="small"
                >
                  <CopyIcon />
                </IconButton>
              ),
              sx: {
                fontFamily: 'monospace',
                fontSize: '0.75rem',
                color: '#f0f6fc',
                backgroundColor: 'rgba(30, 36, 45, 0.5)',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#30363d',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#58a6ff',
                },
              }
            }}
          />
        </Box>

        {copied && (
          <Alert 
            severity="success" 
            sx={{ 
              backgroundColor: 'rgba(35, 134, 54, 0.1)',
              border: '1px solid rgba(35, 134, 54, 0.3)',
              color: '#238636',
              mb: 2
            }}
          >
            Public key copied to clipboard!
          </Alert>
        )}

        <Alert 
          severity="info"
          sx={{ 
            backgroundColor: 'rgba(88, 166, 255, 0.1)',
            border: '1px solid rgba(88, 166, 255, 0.3)',
            color: '#58a6ff'
          }}
        >
          Share this public key with contacts who want to add you. Never share your private key!
        </Alert>
      </DialogContent>

      <DialogActions sx={{ borderTop: '1px solid #30363d', p: 2 }}>
        <Button
          onClick={handleCopyKey}
          startIcon={<CopyIcon />}
          sx={{
            color: '#238636',
            borderColor: '#238636',
            '&:hover': {
              backgroundColor: 'rgba(35, 134, 54, 0.1)',
            }
          }}
          variant="outlined"
        >
          Copy Public Key
        </Button>
        <Button
          onClick={handleClose}
          sx={{
            color: '#f0f6fc',
            backgroundColor: '#30363d',
            '&:hover': {
              backgroundColor: '#373e47',
            }
          }}
        >
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ViewPublicKeyDialog;