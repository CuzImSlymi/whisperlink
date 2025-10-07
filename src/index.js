import React from 'react';
import ReactDOM from 'react-dom/client';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import App from './App';

// Test if React is loading
console.log('React index.js loaded successfully');

// Create dark theme with WhisperLink branding
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#238636',
      light: '#2ea043',
      dark: '#1a6e2a',
    },
    secondary: {
      main: '#f85149',
      light: '#ff6b6b',
      dark: '#da3633',
    },
    background: {
      default: '#0d1117',
      paper: '#161b22',
    },
    surface: {
      primary: '#21262d',
      secondary: '#30363d',
      tertiary: '#484f58',
    },
    text: {
      primary: '#f0f6fc',
      secondary: '#8b949e',
      disabled: '#6e7681',
    },
    divider: '#30363d',
    success: {
      main: '#238636',
    },
    warning: {
      main: '#d29922',
    },
    error: {
      main: '#f85149',
    },
    info: {
      main: '#58a6ff',
    },
  },
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", sans-serif',
    h1: {
      fontSize: '2rem',
      fontWeight: 600,
      letterSpacing: '-0.025em',
    },
    h2: {
      fontSize: '1.5rem',
      fontWeight: 600,
      letterSpacing: '-0.025em',
    },
    h3: {
      fontSize: '1.25rem',
      fontWeight: 600,
      letterSpacing: '-0.025em',
    },
    h4: {
      fontSize: '1.125rem',
      fontWeight: 500,
      letterSpacing: '-0.025em',
    },
    body1: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.75rem',
      lineHeight: 1.4,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarColor: '#484f58 #21262d',
          '&::-webkit-scrollbar, & *::-webkit-scrollbar': {
            backgroundColor: 'transparent',
            width: 8,
          },
          '&::-webkit-scrollbar-thumb, & *::-webkit-scrollbar-thumb': {
            borderRadius: 8,
            backgroundColor: '#484f58',
            minHeight: 24,
          },
          '&::-webkit-scrollbar-thumb:focus, & *::-webkit-scrollbar-thumb:focus': {
            backgroundColor: '#6e7681',
          },
          '&::-webkit-scrollbar-thumb:active, & *::-webkit-scrollbar-thumb:active': {
            backgroundColor: '#6e7681',
          },
          '&::-webkit-scrollbar-thumb:hover, & *::-webkit-scrollbar-thumb:hover': {
            backgroundColor: '#6e7681',
          },
          '&::-webkit-scrollbar-corner, & *::-webkit-scrollbar-corner': {
            backgroundColor: '#21262d',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          padding: '8px 16px',
          fontSize: '0.875rem',
          fontWeight: 500,
          textTransform: 'none',
        },
        containedPrimary: {
          background: 'linear-gradient(135deg, #238636 0%, #2ea043 100%)',
          '&:hover': {
            background: 'linear-gradient(135deg, #2ea043 0%, #238636 100%)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            backgroundColor: '#21262d',
            '& fieldset': {
              borderColor: '#30363d',
            },
            '&:hover fieldset': {
              borderColor: '#484f58',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#238636',
            },
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </React.StrictMode>
);