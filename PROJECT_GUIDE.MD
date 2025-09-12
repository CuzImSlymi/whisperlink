## 🧰 Tech Stack

**Frontend (UI)**
- **Electron**: Desktop app shell  
- **React.js**: Component-based UI  
- **HTML/CSS / Tailwind**: Layout and styling  
- **JavaScript / TypeScript**: Frontend logic  

**Backend (Core Logic)**
- **Python**: Global P2P connections, encryption, message handling  
- **PyNaCl / libsodium**: End-to-end encryption  
- **WebSockets / REST API**: Local communication between frontend and backend  

**Networking**
- **Direct global P2P connections**: Over the Internet  
- **NAT traversal & STUN/hole punching**: To connect devices behind routers/firewalls  
- **Optional future:** Tor hidden service or relay chaining for IP privacy  

## 💬 Features (Current + Future)

**Current (MVP / In Development)**
- One-to-one messaging over global P2P  
- End-to-end encryption  
- Local API to connect Electron frontend to Python backend  
- Python implementation for core WhisperLink logic  

**Future Features**
- Group chats (multi-party encrypted messaging)  
- Offline delivery via trusted peers or optional self-hosted relays  
- Voice & video calls (fully encrypted)  
- IP privacy / anonymity via Tor or relay chaining  
- Metadata minimization (padding, batching, cover traffic)  
- Easy key exchange via QR codes or secure scanning  
- Cross-platform support (Windows, macOS, Linux)  
- Open source, community-driven development  
