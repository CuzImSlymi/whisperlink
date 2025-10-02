# WhisperLink GUI Setup Guide

This guide will help you set up the beautiful dark mode Electron + React GUI for WhisperLink.

## Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Python 3.8+
- The existing WhisperLink Python backend

## Installation Steps

### 1. Install Node.js Dependencies

```bash
npm install
```

### 2. Install Additional Required Packages

```bash
npm install @mui/material @emotion/react @emotion/styled
npm install @mui/icons-material
npm install framer-motion
npm install react-router-dom
npm install axios
```

### 3. Development Dependencies

```bash
npm install --save-dev electron electron-builder concurrently wait-on
```

### 4. Update Python Bridge

Make sure the Python bridge can communicate with your existing backend:

```bash
# Test the Python bridge
python3 python_bridge.py
```

## Running the Application

### Development Mode

1. Start the React development server:
```bash
npm start
```

2. In another terminal, start Electron:
```bash
npm run electron-dev
```

Or use the combined command:
```bash
npm run dev
```

### Production Build

```bash
npm run build
npm run electron-pack
```

## Features

### ✨ Beautiful Dark Theme
- GitHub-inspired dark color scheme
- Smooth animations and transitions
- Glass morphism effects
- Responsive layout

### 🔐 Security-First Design
- End-to-end encryption indicators
- Secure connection status
- Privacy-focused UI elements

### 💬 Chat Interface
- Real-time messaging
- Message status indicators
- Typing indicators (ready for implementation)
- File sharing support (ready for implementation)

### 👥 Contact Management
- Add contacts with public keys
- Direct and tunnel connections
- Contact status indicators
- Easy contact removal

### ⚙️ Settings Panel
- Server management
- User preferences
- Connection settings
- About information

## Architecture

```
WhisperLink GUI
├── Electron Main Process
│   ├── Window management
│   ├── Python bridge communication
│   └── System integration
├── React Renderer Process
│   ├── Authentication (Login/Register)
│   ├── Main Interface
│   │   ├── Sidebar (Chats/Contacts/Settings)
│   │   └── Chat Area
│   └── UI Components
└── Python Backend Bridge
    ├── User management
    ├── Contact management
    ├── Connection handling
    └── Message encryption
```

## Customization

### Themes
The dark theme can be customized in `src/index.js`:

```javascript
const darkTheme = createTheme({
  palette: {
    primary: { main: '#238636' }, // Change primary color
    background: { default: '#0d1117' }, // Change background
    // ... other theme options
  }
});
```

### Window Settings
Modify window behavior in `electron/main.js`:

```javascript
const mainWindow = new BrowserWindow({
  width: 1200,
  height: 800,
  // ... other window options
});
```

## Troubleshooting

### Common Issues

1. **Electron not starting**
   - Make sure all dependencies are installed
   - Check Node.js version compatibility

2. **Python bridge connection fails**
   - Verify Python path in `electron/main.js`
   - Check if required Python packages are installed

3. **UI elements not displaying correctly**
   - Clear browser cache
   - Restart development server

### Debug Mode

Enable debug mode by setting environment variable:
```bash
export ELECTRON_IS_DEV=true
npm run electron
```

## Integration with Existing Backend

The GUI integrates with your existing WhisperLink Python backend through:

1. **Python Bridge** (`python_bridge.py`)
   - Handles communication between Electron and Python
   - Manages user authentication
   - Processes contact operations
   - Handles message encryption/decryption

2. **Existing Managers**
   - Uses `UserManager` for authentication
   - Uses `ContactManager` for contact operations
   - Uses `ConnectionManager` for P2P connections
   - Uses `CryptoManager` for encryption

## Security Considerations

- All sensitive operations remain in Python backend
- GUI only handles display and user input
- Private keys never leave the Python process
- All communication uses encrypted channels

## Future Enhancements

- [ ] Voice/Video call interface
- [ ] File transfer with progress indicators
- [ ] Group chat support
- [ ] Mobile-responsive design
- [ ] Custom notification sounds
- [ ] Backup/restore functionality
- [ ] Plugin system

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the console logs
3. Open an issue on the project repository

---

**WhisperLink GUI** - Secure, Private, Beautiful 🔒✨