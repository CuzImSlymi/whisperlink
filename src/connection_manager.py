import os
import uuid
import json
import socket
import threading
import subprocess
import asyncio
import websockets
import ssl
import urllib.parse
import aiohttp
import requests
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .models import Connection, Contact, User
from .user_manager import UserManager
from .contact_manager import ContactManager
from .crypto_manager import CryptoManager

class TunnelManager:
    """Manages tunnel connections for privacy using ngrok only"""
    
    def __init__(self):
        self.active_tunnels: Dict[int, str] = {}  # port -> tunnel_url
        self.ws_bridge_port = 9002  # WebSocket bridge port
        self.ws_bridge_running = False
        self.ws_bridge_server = None
        self.ngrok_process = None

    def create_tunnel(self, local_port: int) -> Optional[str]:
        """Create a tunnel to expose local port using ngrok only"""
        try:
            # Start WebSocket bridge if not running
            if not self.ws_bridge_running:
                print(f"Starting WebSocket bridge for port {local_port}")
                if not self._start_websocket_bridge(local_port):
                    print("❌ Failed to start WebSocket bridge")
                    return None
                
            # Try ngrok only - no fallbacks
            return self._create_ngrok_tunnel(local_port)
            
        except Exception as e:
            print(f"❌ Tunnel creation failed: {e}")
            return None

    def _create_ngrok_tunnel(self, local_port: int) -> Optional[str]:
        """Create ngrok tunnel - fail if it doesn't work"""
        try:
            print("Starting ngrok tunnel...")
            
            # Kill any existing ngrok processes first
            self._kill_existing_ngrok()
            
            # Start ngrok process
            self.ngrok_process = subprocess.Popen([
                'ngrok', 'http', str(self.ws_bridge_port), '--log=stdout'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Give ngrok time to start and establish tunnel
            print("Waiting for ngrok to establish tunnel...")
            time.sleep(8)  # Longer wait for ngrok
            
            # Get tunnel URL from ngrok API
            tunnel_url = self._get_ngrok_tunnel_url()
            
            if tunnel_url:
                print(f"✅ ngrok tunnel created: {tunnel_url}")
                
                # Test the tunnel
                if self._test_tunnel_connectivity(tunnel_url):
                    self.active_tunnels[local_port] = tunnel_url
                    return tunnel_url
                else:
                    print("❌ Tunnel created but not responding")
                    self._kill_existing_ngrok()
                    return None
            else:
                print("❌ Failed to get tunnel URL from ngrok")
                self._kill_existing_ngrok()
                return None
                
        except FileNotFoundError:
            print("❌ ngrok not found. Please install ngrok:")
            print("   Download from https://ngrok.com/download")
            print("   Or install: brew install ngrok (macOS) / choco install ngrok (Windows)")
            return None
        except Exception as e:
            print(f"❌ ngrok error: {e}")
            self._kill_existing_ngrok()
            return None

    def _kill_existing_ngrok(self):
        """Kill any existing ngrok processes"""
        try:
            if self.ngrok_process:
                self.ngrok_process.terminate()
                self.ngrok_process.wait(timeout=5)
                self.ngrok_process = None
        except:
            pass
        
        # Also try to kill via system command
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['taskkill', '/f', '/im', 'ngrok.exe'], capture_output=True)
            else:  # Unix-like
                subprocess.run(['pkill', '-f', 'ngrok'], capture_output=True)
        except:
            pass

    def _get_ngrok_tunnel_url(self) -> Optional[str]:
        """Get tunnel URL from ngrok local API"""
        try:
            # ngrok exposes a local API on port 4040
            response = requests.get('http://localhost:4040/api/tunnels', timeout=10)
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get('tunnels', [])
                for tunnel in tunnels:
                    if tunnel.get('proto') == 'https':
                        return tunnel.get('public_url')
            return None
        except Exception as e:
            print(f"Failed to get ngrok tunnel URL: {e}")
            return None

    def _test_tunnel_connectivity(self, tunnel_url: str) -> bool:
        """Test if tunnel is responsive"""
        try:
            print("Testing tunnel connectivity...")
            response = requests.get(tunnel_url, timeout=15)
            print(f"Tunnel test: HTTP {response.status_code}")
            return response.status_code < 500
        except Exception as e:
            print(f"Tunnel test failed: {e}")
            return False

    def _start_websocket_bridge(self, tcp_port: int) -> bool:
        """Start WebSocket bridge to forward to TCP server"""
        def run_bridge():
            async def handle_ws_client(websocket, path):
                try:
                    print(f"WebSocket client connected from {websocket.remote_address}")
                    # Connect to the local TCP server
                    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    tcp_sock.settimeout(10)
                    try:
                        tcp_sock.connect(('127.0.0.1', tcp_port))
                        print(f"Connected to TCP server at 127.0.0.1:{tcp_port}")
                    except Exception as e:
                        print(f"Failed to connect to TCP server: {e}")
                        tcp_sock.close()
                        return
                    
                    async def tcp_to_ws():
                        try:
                            loop = asyncio.get_event_loop()
                            while True:
                                # Use asyncio to read from socket without blocking
                                data = await loop.run_in_executor(None, tcp_sock.recv, 4096)
                                if not data:
                                    break
                                await websocket.send(data)
                        except Exception as e:
                            print(f"TCP->WS error: {e}")
                        finally:
                            tcp_sock.close()

                    async def ws_to_tcp():
                        try:
                            async for message in websocket:
                                if isinstance(message, bytes):
                                    tcp_sock.sendall(message)
                                else:
                                    tcp_sock.sendall(message.encode() if isinstance(message, str) else message)
                        except Exception as e:
                            print(f"WS->TCP error: {e}")
                        finally:
                            tcp_sock.close()
                    
                    # Run both directions concurrently
                    await asyncio.gather(
                        tcp_to_ws(),
                        ws_to_tcp(),
                        return_exceptions=True
                    )
                    
                except Exception as e:
                    print(f"Bridge connection error: {e}")

            async def main():
                print(f"Starting WebSocket bridge on 0.0.0.0:{self.ws_bridge_port} -> 127.0.0.1:{tcp_port}")
                try:
                    self.ws_bridge_server = await websockets.serve(
                        handle_ws_client, 
                        '0.0.0.0', 
                        self.ws_bridge_port,
                        ping_interval=30,
                        ping_timeout=15,
                        max_size=1048576,  # 1MB max message size
                        compression=None   # Disable compression for tunnel compatibility
                    )
                    self.ws_bridge_running = True
                    print(f"✅ WebSocket bridge running on port {self.ws_bridge_port}")
                    await self.ws_bridge_server.wait_closed()
                except Exception as e:
                    print(f"❌ Failed to start WebSocket bridge: {e}")
                    self.ws_bridge_running = False

            try:
                asyncio.run(main())
            except Exception as e:
                print(f"❌ WebSocket bridge error: {e}")
                self.ws_bridge_running = False

        bridge_thread = threading.Thread(target=run_bridge, daemon=True)
        bridge_thread.start()
        
        # Wait for bridge to start and verify it's running
        print("Waiting for WebSocket bridge to start...")
        time.sleep(3)
        
        # Verify bridge is running
        max_retries = 5
        for i in range(max_retries):
            try:
                test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_sock.settimeout(1)
                result = test_sock.connect_ex(('127.0.0.1', self.ws_bridge_port))
                test_sock.close()
                if result == 0:
                    print(f"✅ WebSocket bridge verified running on port {self.ws_bridge_port}")
                    return True
            except:
                pass
            
            if i < max_retries - 1:
                print(f"Waiting for WebSocket bridge... ({i+1}/{max_retries})")
                time.sleep(2)
            else:
                print("❌ WebSocket bridge failed to start")
                return False
        
        return False

    def close_tunnel(self, local_port: int):
        """Close an active tunnel"""
        if local_port in self.active_tunnels:
            del self.active_tunnels[local_port]
            
        # Kill ngrok process
        self._kill_existing_ngrok()
            
        if self.ws_bridge_server:
            try:
                self.ws_bridge_server.close()
            except:
                pass
            self.ws_bridge_running = False

    def get_tunnel_url(self, local_port: int) -> Optional[str]:
        """Get tunnel URL for a local port"""
        return self.active_tunnels.get(local_port)


class ConnectionManager:
    """Manages P2P connections with other peers"""
    
    def __init__(self, user_manager: UserManager, contact_manager: ContactManager):
        self.user_manager = user_manager
        self.contact_manager = contact_manager
        self.tunnel_manager = TunnelManager()
        self.connections: Dict[str, Connection] = {}
        self.server_socket: Optional[socket.socket] = None
        self.server_port: Optional[int] = None
        self.listening = False
        self.message_handlers: List[callable] = []

    def add_message_handler(self, handler: callable):
        """Add a message handler function"""
        self.message_handlers.append(handler)

    def start_listening(self, port: int = 0, use_tunnel: bool = False) -> Tuple[bool, str]:
        """Start listening for incoming connections"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', port))
            self.server_socket.listen(5)
            
            # Get the actual port if 0 was specified
            self.server_port = self.server_socket.getsockname()[1]
            self.listening = True
            
            # Start listening thread
            listen_thread = threading.Thread(target=self._listen_for_connections, daemon=True)
            listen_thread.start()
            
            connection_info = f"localhost:{self.server_port}"
            
            if use_tunnel:
                print("Creating secure tunnel (this may take a moment)...")
                tunnel_url = self.tunnel_manager.create_tunnel(self.server_port)
                if tunnel_url:
                    connection_info = tunnel_url
                else:
                    # Stop listening since tunnel failed
                    self.stop_listening()
                    return False, "❌ Failed to create tunnel. Try direct IP connection instead."
                    
            return True, connection_info
            
        except Exception as e:
            return False, f"❌ Failed to start listening: {str(e)}"

    def stop_listening(self):
        """Stop listening for connections"""
        self.listening = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
            
        # Close any active tunnels
        if self.server_port:
            self.tunnel_manager.close_tunnel(self.server_port)

    def _listen_for_connections(self):
        """Listen for incoming connections (runs in background thread)"""
        while self.listening and self.server_socket:
            try:
                client_socket, client_address = self.server_socket.accept()
                
                # Handle new connection in separate thread
                handle_thread = threading.Thread(
                    target=self._handle_incoming_connection,
                    args=(client_socket, client_address),
                    daemon=True
                )
                handle_thread.start()
                
            except Exception as e:
                if self.listening:  # Only log if we're supposed to be listening
                    print(f"Error accepting connection: {e}")
                break

    def _handle_incoming_connection(self, client_socket: socket.socket, client_address: tuple):
        """Handle an incoming connection"""
        try:
            # Receive initial handshake
            handshake_data = client_socket.recv(1024).decode()
            handshake = json.loads(handshake_data)
            
            peer_id = handshake.get('user_id')
            peer_username = handshake.get('username')
            peer_public_key = handshake.get('public_key')
            
            if not all([peer_id, peer_username, peer_public_key]):
                client_socket.close()
                return
                
            # Send our handshake response
            current_user = self.user_manager.get_current_user()
            if not current_user:
                client_socket.close()
                return
                
            response = {
                'user_id': current_user.user_id,
                'username': current_user.username,
                'public_key': current_user.public_key,
                'status': 'accepted'
            }
            client_socket.send(json.dumps(response).encode())
            
            # Create connection object
            connection = Connection(
                peer_id=peer_id,
                peer_username=peer_username,
                connection_type="incoming",
                address=client_address[0],
                port=client_address[1],
                status="connected",
                established_at=datetime.now().isoformat(),
                socket_obj=client_socket
            )
            self.connections[peer_id] = connection
            
            # Update contact last seen
            self.contact_manager.update_contact_last_seen(peer_id)
            
            print(f"\n✅ Incoming connection established with {peer_username}")
            
            # Handle messages from this peer
            self._handle_peer_messages(peer_id)
            
        except Exception as e:
            print(f"Error handling incoming connection: {e}")
            try:
                client_socket.close()
            except:
                pass

    def connect_to_peer(self, peer_id: str) -> bool:
        """Connect to a peer"""
        contact = self.contact_manager.get_contact(peer_id)
        if not contact:
            return False
            
        current_user = self.user_manager.get_current_user()
        if not current_user:
            return False
            
        try:
            if contact.connection_type == "direct" and contact.address:
                # Direct IP connection
                return self._connect_direct(peer_id, contact, current_user)
            elif contact.connection_type == "tunnel" and contact.tunnel_url:
                # Tunnel connection
                return self._connect_via_tunnel(peer_id, contact, current_user)
            else:
                return False
                
        except Exception as e:
            print(f"❌ Failed to connect to peer: {e}")
            return False

    def _connect_direct(self, peer_id: str, contact: Contact, current_user: User) -> bool:
        """Connect to peer via direct IP"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)
            
            host, port = contact.address.split(':')
            client_socket.connect((host, int(port)))
            
            # Send handshake
            handshake = {
                'user_id': current_user.user_id,
                'username': current_user.username,
                'public_key': current_user.public_key
            }
            client_socket.send(json.dumps(handshake).encode())
            
            # Receive handshake response
            response_data = client_socket.recv(1024).decode()
            response = json.loads(response_data)
            
            if response.get('status') != 'accepted':
                client_socket.close()
                return False
                
            # Create connection object
            connection = Connection(
                peer_id=peer_id,
                peer_username=contact.username,
                connection_type="outgoing",
                address=contact.address or "",
                port=0,
                status="connected",
                established_at=datetime.now().isoformat(),
                socket_obj=client_socket
            )
            self.connections[peer_id] = connection
            
            # Start message handling thread
            message_thread = threading.Thread(
                target=self._handle_peer_messages,
                args=(peer_id,),
                daemon=True
            )
            message_thread.start()
            
            print(f"✅ Successfully connected to {contact.username}")
            return True
            
        except Exception as e:
            print(f"❌ Direct connection failed: {e}")
            try:
                client_socket.close()
            except:
                pass
            return False

    def _connect_via_tunnel(self, peer_id: str, contact: Contact, current_user: User) -> bool:
        """Connect to peer via tunnel"""
        print(f"Connecting to {contact.username} via tunnel...")
        try:
            # Prepare handshake data
            handshake = {
                'user_id': current_user.user_id,
                'username': current_user.username,
                'public_key': current_user.public_key
            }
            
            # Run the async connection in a separate thread
            result = [False]  # Use list to modify from inner function
            
            def run_async_connect():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result[0] = loop.run_until_complete(self._async_tunnel_connect(peer_id, contact, handshake))
                except Exception as e:
                    print(f"❌ Tunnel connection error: {e}")
                    result[0] = False
                finally:
                    loop.close()
            
            connect_thread = threading.Thread(target=run_async_connect, daemon=True)
            connect_thread.start()
            connect_thread.join(timeout=30)  # 30 second timeout
            
            return result[0]
            
        except Exception as e:
            print(f"❌ Tunnel connection failed: {e}")
            return False

    async def _async_tunnel_connect(self, peer_id: str, contact: Contact, handshake: dict) -> bool:
        """Establish connection via tunnel"""
        try:
            tunnel_url = contact.tunnel_url.rstrip('/')
            print(f"Connecting to: {tunnel_url}")
            
            # Try WebSocket connection only
            return await self._try_websocket_connection(peer_id, contact, handshake, tunnel_url)
            
        except Exception as e:
            print(f"❌ Tunnel connection error: {e}")
            return False

    async def _try_websocket_connection(self, peer_id: str, contact: Contact, handshake: dict, tunnel_url: str):
        """Try WebSocket connection"""
        import websockets
        
        # Convert to WebSocket URL
        ws_url = tunnel_url.replace('https://', 'wss://').replace('http://', 'ws://')
        
        # Headers for ngrok
        headers = {
            'User-Agent': 'WhisperLink/1.0',
            'Origin': tunnel_url
        }
        
        # Create SSL context for HTTPS tunnels
        ssl_context = None
        if ws_url.startswith('wss://'):
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        
        print(f"Attempting WebSocket connection to: {ws_url}")
        
        try:
            # Try connection with timeout
            websocket = await asyncio.wait_for(
                websockets.connect(
                    ws_url,
                    additional_headers=headers,
                    ssl=ssl_context,
                    open_timeout=20,
                    ping_interval=30,
                    ping_timeout=15,
                    max_size=1048576,
                    compression=None
                ),
                timeout=25.0
            )
            
            # Send handshake
            await websocket.send(json.dumps(handshake))
            
            # Wait for response with timeout
            response_data = await asyncio.wait_for(websocket.recv(), timeout=15.0)
            response = json.loads(response_data)
            
            if response.get('status') == 'accepted':
                # Create connection object
                connection = Connection(
                    peer_id=peer_id,
                    peer_username=contact.username,
                    connection_type="tunnel_websocket",
                    address="tunnel",
                    port=0,
                    status="connected",
                    established_at=datetime.now().isoformat(),
                    websocket_obj=websocket
                )
                self.connections[peer_id] = connection
                
                # Update contact last seen
                self.contact_manager.update_contact_last_seen(peer_id)
                
                print(f"✅ Successfully connected to {contact.username} via tunnel")
                
                # Handle messages in background
                asyncio.create_task(self._handle_websocket_messages_native(peer_id, websocket))
                return True
            else:
                await websocket.close()
                print("❌ Handshake rejected by peer")
                return False
                
        except Exception as e:
            print(f"❌ WebSocket connection failed: {e}")
            return False

    def _handle_peer_messages(self, peer_id: str):
        """Handle messages from a connected peer"""
        connection = self.connections.get(peer_id)
        if not connection or not connection.socket_obj:
            return
            
        try:
            while connection.status == "connected":
                # Receive message
                data = connection.socket_obj.recv(4096)
                if not data:
                    break
                    
                try:
                    message_data = json.loads(data.decode())
                    message_type = message_data.get('type')
                    
                    if message_type == 'chat':
                        encrypted_message = message_data.get('message')
                        timestamp = message_data.get('timestamp')
                        
                        # Decrypt message
                        current_user = self.user_manager.get_current_user()
                        contact = self.contact_manager.get_contact(peer_id)
                        
                        if current_user and contact:
                            crypto = CryptoManager()
                            decrypted_message = crypto.decrypt_message(
                                current_user.private_key,
                                contact.public_key,
                                encrypted_message
                            )
                            
                            # Call message handlers
                            for handler in self.message_handlers:
                                handler(peer_id, connection.peer_username, decrypted_message, timestamp)
                                
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            print(f"Error handling messages from {peer_id}: {e}")
        finally:
            # Connection closed
            connection.status = "disconnected"
            try:
                connection.socket_obj.close()
            except:
                pass

    async def _handle_websocket_messages_native(self, peer_id: str, websocket):
        """Handle messages from native WebSocket connection"""
        try:
            async for message in websocket:
                try:
                    message_data = json.loads(message)
                    message_type = message_data.get('type')
                    
                    if message_type == 'chat':
                        encrypted_message = message_data.get('message')
                        timestamp = message_data.get('timestamp')
                        
                        # Decrypt message
                        current_user = self.user_manager.get_current_user()
                        contact = self.contact_manager.get_contact(peer_id)
                        
                        if current_user and contact:
                            crypto = CryptoManager()
                            decrypted_message = crypto.decrypt_message(
                                current_user.private_key,
                                contact.public_key,
                                encrypted_message
                            )
                            
                            # Call message handlers
                            for handler in self.message_handlers:
                                handler(peer_id, contact.username, decrypted_message, timestamp)
                                
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            print(f"Error handling WebSocket messages from {peer_id}: {e}")
        finally:
            # Connection closed
            if peer_id in self.connections:
                self.connections[peer_id].status = "disconnected"
                del self.connections[peer_id]

    def send_message(self, peer_id: str, message: str) -> bool:
        """Send an encrypted message to a peer"""
        connection = self.connections.get(peer_id)
        if not connection or connection.status != "connected":
            return False
            
        current_user = self.user_manager.get_current_user()
        contact = self.contact_manager.get_contact(peer_id)
        
        if not current_user or not contact:
            return False
            
        try:
            # Encrypt message
            crypto = CryptoManager()
            encrypted_message = crypto.encrypt_message(
                current_user.private_key,
                contact.public_key,
                message
            )
            
            # Create message packet
            message_data = {
                'type': 'chat',
                'message': encrypted_message,
                'timestamp': datetime.now().isoformat()
            }
            
            # Send message based on connection type
            if connection.websocket_obj:
                # WebSocket connection - run async send
                asyncio.create_task(self._send_websocket_message(connection.websocket_obj, message_data))
                return True
            elif connection.socket_obj:
                # Socket connection
                connection.socket_obj.send(json.dumps(message_data).encode())
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Failed to send message: {e}")
            return False

    async def _send_websocket_message(self, websocket, message_data):
        """Send message via WebSocket"""
        try:
            await websocket.send(json.dumps(message_data))
        except Exception as e:
            print(f"❌ Failed to send WebSocket message: {e}")

    def disconnect_from_peer(self, peer_id: str):
        """Disconnect from a peer"""
        connection = self.connections.get(peer_id)
        if connection:
            connection.status = "disconnected"
            
            if connection.socket_obj:
                try:
                    connection.socket_obj.close()
                except:
                    pass
                    
            if connection.websocket_obj:
                try:
                    asyncio.create_task(connection.websocket_obj.close())
                except:
                    pass
                    
            del self.connections[peer_id]

    def get_active_connections(self) -> List[Connection]:
        """Get list of active connections"""
        return [conn for conn in self.connections.values() if conn.status == "connected"]

    def get_connection(self, peer_id: str) -> Optional[Connection]:
        """Get connection by peer ID"""
        return self.connections.get(peer_id)
