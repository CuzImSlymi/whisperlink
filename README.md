# WhisperLink

<div align="center">

![WhisperLink Logo](https://img.shields.io/badge/WhisperLink-Secure%20P2P%20Messenger-blue?style=for-the-badge&logo=shield&logoColor=white)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg?style=flat-square)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat-square&logo=react&logoColor=black)](https://reactjs.org)
[![Electron](https://img.shields.io/badge/Electron-27+-47848F?style=flat-square&logo=electron&logoColor=white)](https://electronjs.org)

**A serverless, peer-to-peer messenger focused on maximum privacy and encryption**

Built to resist surveillance and protect conversations from mass scanning or government backdoors.

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Development](#development) • [Contributing](#contributing)

</div>

---

## Features

### Core Functionality
- **🔐 End-to-End Encryption** - Only intended recipients can read messages
- **🌐 Peer-to-Peer Messaging** - Secure messaging without central servers  
- **🛡️ Privacy-First Design** - Metadata minimization and traffic analysis protection
- **💻 Cross-Platform Support** - Works on Windows, macOS, and Linux
- **🔑 Secure Key Exchange** - Easy contact management with public key verification

### Current Status
- ✅ MVP with encrypted one-to-one messaging
- ✅ Direct P2P connections (LAN/Wi-Fi/Internet)
- ✅ GUI application with dark mode interface
- ✅ Tunnel support for internet connections
- ⚙️ **Active Development** - New features being added regularly

### Roadmap
- 👥 Group chats with encrypted multi-party messaging
- 📦 Offline delivery using trusted peers or self-hosted relays
- 🕵️‍♂️ Tor hidden service integration for IP privacy
- 🎤📹 Voice & video calls with full encryption
- 📱 Mobile client applications

## Technology Stack

- **Backend:** Python 3.8+ with PyNaCl/libsodium encryption
- **Frontend:** React 18+ with Material-UI components
- **Desktop:** Electron 27+ for cross-platform GUI
- **Networking:** WebSocket and TCP for P2P connections
- **Security:** Argon2id key derivation, NaCl SecretBox encryption

## Installation

### Prerequisites

Make sure you have the following installed:
- **Python 3.8+** ([Download](https://python.org/downloads/))
- **Node.js 16+** ([Download](https://nodejs.org/))
- **Git** ([Download](https://git-scm.com/))

### Quick Install

#### Windows
```powershell
# Clone the repository
git clone https://github.com/CuzImSlymi/whisperlink.git
cd whisperlink

# Create Python virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install
```

#### macOS / Linux
```bash
# Clone the repository
git clone https://github.com/CuzImSlymi/whisperlink.git
cd whisperlink

# Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install
```

### Verify Installation
```bash
# Test Python backend
python main.py --help

# Test Node.js frontend
npm run build
```

## Usage

### GUI Application (Recommended)

Start the complete GUI application:

```bash
# Windows
.venv\Scripts\activate
npm run dev

# macOS / Linux  
source .venv/bin/activate
npm run dev
```

This will:
1. Start the React development server (port 3000)
2. Launch the Electron desktop application
3. Initialize the Python backend automatically

### Command Line Interface

For advanced users or testing:

#### 1. Register User Accounts
```bash
# Activate virtual environment first
python main.py

# Follow the prompts to:
# - Create a new account with username/password
# - Or login to existing account
```

#### 2. Start Listening for Connections

**Direct Connection (LAN):**
```bash
# In the main menu, choose option 1
# Your local IP and port will be displayed
# Share this information with contacts
```

**Tunnel Connection (Internet):**
```bash
# In the main menu, choose option 2
# A public tunnel URL will be created
# Share this URL with remote contacts
```

#### 3. Connect to Contacts

**Add Contact:**
```bash
# In the main menu, choose option 3
# Enter contact's connection details:
# - Username
# - Public key
# - Connection address (IP:port or tunnel URL)
```

**Send Messages:**
```bash
# Choose a contact from your list
# Type messages in real-time
# All messages are end-to-end encrypted
```

### Advanced Configuration

#### Environment Variables
```bash
# Optional: Set custom ports
export WHISPERLINK_WS_PORT=9002
export WHISPERLINK_TCP_PORT=9001

# Optional: Set data directory
export WHISPERLINK_DATA_DIR="./custom-data"
```

#### Manual Tunnel Setup
```bash
# Install ngrok (optional)
npm install -g ngrok

# Or use other tunnel services:
# - loca.lt
# - serveo.net  
# - localhost.run
```

## Development

### Project Structure
```
whisperlink/
├── src/                    # React frontend components
│   ├── components/         # UI components
│   ├── context/           # React context providers
│   └── App.js             # Main React application
├── electron/              # Electron main process
├── whisperlink/           # Python package
├── main.py               # Python CLI entry point
├── requirements.txt      # Python dependencies
├── package.json         # Node.js dependencies
└── README.md           # This file
```

### Development Commands

```bash
# Start development server only
npm start

# Start Electron in development mode
npm run electron-dev

# Run both React and Electron together
npm run dev

# Build for production
npm run build
npm run electron-pack

# Stop all development servers
npm run stop
```

### Building from Source

#### Frontend Build
```bash
npm run build
```

#### Backend Package
```bash
python setup.py sdist bdist_wheel
```

#### Desktop Application
```bash
npm run electron-pack
```

The built application will be in the `dist/` directory.

## Security Features

- **🔐 PyNaCl Encryption** - Industry-standard NaCl cryptography
- **🔑 Argon2id Key Derivation** - Resistant to GPU cracking attacks  
- **🛡️ Perfect Forward Secrecy** - Past messages stay secure
- **🚫 Zero Server Storage** - No messages stored on servers
- **🔒 Local Key Storage** - Private keys never leave your device
- **⚡ Real-time Encryption** - All messages encrypted before transmission

## Troubleshooting

### Common Issues

**Python Import Errors:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Node.js Build Errors:**
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

**Connection Issues:**
- Check firewall settings allow the application
- Verify network connectivity between peers
- Try different tunnel services if ngrok fails

### Debug Mode
```bash
# Enable debug logging
export WHISPERLINK_DEBUG=1
npm run dev
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Start for Contributors
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Submit a pull request with a clear description

### Development Setup
```bash
# Clone your fork
git clone https://github.com/CuzImSlymi/whisperlink.git
cd whisperlink

# Add upstream remote
git remote add upstream https://github.com/CuzImSlymi/whisperlink.git

# Install development dependencies
pip install -r requirements.txt
npm install
```

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

See [LICENSE](docs/LICENSE) for the full license text.

## Contributors

- **Slymi** - Lead Developer
- **CLPD** - Core Contributor

## Support

- 📚 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/CuzImSlymi/whisperlink/issues)
- 💬 [Discussions](https://github.com/CuzImSlymi/whisperlink/discussions)

---

<div align="center">

**Built with privacy in mind. Your conversations, your control.**

[⭐ Star this project](https://github.com/CuzImSlymi/whisperlink) if you find it useful!

</div>
