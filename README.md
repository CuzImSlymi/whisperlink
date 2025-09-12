# WhisperLink 🔒💬

**WhisperLink** is a serverless, peer-to-peer messenger focused on maximum privacy and encryption. Built to resist surveillance and protect conversations from mass scanning or government backdoors.

Currently, WhisperLink is in **active development** ⚙️.

## Current Status 🛠️

- MVP in development
- Core functionality: encrypted one-to-one messaging over direct P2P connections 🔐
- Python implementation 🐍 for easy prototyping and cross-platform compatibility

## Future Features / Roadmap 🚀

- **Peer-to-Peer Messaging:** Secure messaging without central servers 🌐
- **End-to-End Encryption:** Only intended recipients can read messages 🔏
- **Group Chats:** Encrypted multi-party messaging 👥
- **Offline Delivery:** Store-and-forward using trusted peers or optional self-hosted relays 📦
- **IP Privacy / Anonymity:** Optional Tor hidden service integration 🕵️‍♂️
- **Voice & Video Calls:** Fully encrypted real-time communication 🎤📹
- **Cross-Platform Support:** Desktop and mobile clients 💻📱
- **Metadata Minimization:** Protect against traffic analysis 🛡️
- **Easy Key Exchange:** QR codes or secure scanning 🔑

## Technology Stack 🧰

- **Programming Language:** Python 🐍  
- **Encryption Libraries:** PyNaCl / libsodium 🔐  
- **Networking:** Direct peer-to-peer connections (LAN/Wi-Fi/Internet) 🌐  

## MVP Quickstart (Local test) ⚡

1. Create a virtualenv and install dependencies
```bash
cd /Users/a10324/whisperlink
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2. Register two identities
```bash
python -m whisperlink register --name Alice --password passA
python -m whisperlink register --name Bob --password passB
```

3. Start Bob's listener (use Alice's public key as the peer key)
```bash
python -m whisperlink start-server \
  --port 9001 \
  --store .whisperlink/Bob \
  --password passB \
  --peer-key $(cat .whisperlink/Alice/public.key)
```

4. From another terminal, connect from Alice (use Bob's public key) and send a message
```bash
python -m whisperlink connect \
  --host 127.0.0.1 \
  --port 9001 \
  --store .whisperlink/Alice \
  --password passA \
  --peer-key $(cat .whisperlink/Bob/public.key) \
  --message "hello from Alice"
```

You should see Bob print the received plaintext and Alice receive an "ack" reply.

## Tunnel Support (Internet) 🌐

For friends in different locations, use a tunnel service:

1. Start your TCP server as above
2. Start the WebSocket bridge:
```bash
python -m whisperlink start-ws-bridge --tcp-port 9001 --ws-port 9002
```
3. Expose the bridge via tunnel (e.g., ngrok, loca.lt):
```bash
# Using ngrok
ngrok http 9002

# Using loca.lt (if you have it)
# Point your tunnel to localhost:9002
```
4. Friend connects using the tunnel URL:
```bash
python -m whisperlink connect \
  --store .whisperlink/FriendName \
  --password friendPass \
  --peer-key "YOUR_PUBLIC_KEY" \
  --ws-url "https://your-tunnel-url.loca.lt" \
  --message "hello via tunnel"
```

Notes:
- Private keys are encrypted at rest with Argon2id-derived keys and SecretBox.
- WebSocket bridge forwards encrypted data between tunnel and local TCP server.
- Tunnel services see encrypted traffic only; your IP is visible to the tunnel provider.

## Contributors 👨‍💻👩‍💻

- **Slymi**  
- **CLPD**

## License 📄

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**. See [LICENSE](LICENSE) for details.
