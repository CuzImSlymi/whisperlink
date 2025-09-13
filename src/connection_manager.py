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
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .models import Connection, Contact, User
from .user_manager import UserManager
from .contact_manager import ContactManager
from .crypto_manager import CryptoManager

class TunnelManager:
    """Manages tunnel connections for privacy using a direct WebSocket server."""

    def __init__(self, connection_handler: callable):
        self.active_tunnel_url: Optional[str] = None
        self.ws_server_port = 9002
        self.ws_server_running = False
        self._connection_handler = connection_handler
        self._stop_server_event = asyncio.Event()
        self.server_loop: Optional[asyncio.AbstractEventLoop] = None

    def create_tunnel(self) -> Optional[str]:
        """Create a tunnel to expose the WebSocket server."""
        try:
            if not self.ws_server_running:
                print(f"Starting WebSocket server for tunneling on port {self.ws_server_port}")
                self._start_websocket_server()

            # Use localtunnel to expose the WebSocket server port
            print(f"Attempting to create tunnel for port {self.ws_server_port}")
            result = subprocess.run(
                ['npx', 'localtunnel', '--port', str(self.ws_server_port)],
                capture_output=True, text=True, timeout=15
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'https://' in line:
                        self.active_tunnel_url = line.strip()
                        print(f"✅ Tunnel created: {self.active_tunnel_url}")
                        return self.active_tunnel_url
            
            # Localtunnel command failed
            print(f"❌ Localtunnel command failed. Stderr: {result.stderr.strip()}")
            print("   Please ensure 'localtunnel' is installed and accessible:")
            print("   npm install -g localtunnel")
            return None

        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ `localtunnel` command not found or timed out.")
            print("   Please ensure Node.js is installed and that 'localtunnel' is installed globally:")
            print("   npm install -g localtunnel")
            return None

    def _start_websocket_server(self):
        """Starts the native WebSocket server in a background thread."""
        def run_server():
            async def main():
                server = await websockets.serve(
                    self._connection_handler, '0.0.0.0', self.ws_server_port
                )
                self.ws_server_running = True
                print(f"WebSocket server listening on 0.0.0.0:{self.ws_server_port}")

                # Wait until the stop event is set
                await self._stop_server_event.wait()

                # Gracefully shut down the server
                server.close()
                await server.wait_closed()
                self.ws_server_running = False
                print("WebSocket server stopped.")

            try:
                # Set a new event loop for this thread
                self.server_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.server_loop)
                self.server_loop.run_until_complete(main())
            except Exception as e:
                print(f"WebSocket server error: {e}")
                self.ws_server_running = False

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        import time
        time.sleep(1)  # Give it a moment to start up

    def close_tunnel(self):
        """Stops the WebSocket server."""
        if self.ws_server_running:
            # Signal the server to stop
            self._stop_server_event.set()
        self.active_tunnel_url = None

    def get_tunnel_url(self) -> Optional[str]:
        """Get the active tunnel URL."""
        return self.active_tunnel_url

class ConnectionManager:
    """Manages P2P connections with other peers"""
    
    def __init__(self, user_manager: UserManager, contact_manager: ContactManager):
        self.user_manager = user_manager
        self.contact_manager = contact_manager
        self.tunnel_manager = TunnelManager(self._handle_incoming_websocket_connection)
        self.connections: Dict[str, Connection] = {}
        self.server_socket: Optional[socket.socket] = None
        self.server_port: Optional[int] = None
        self.listening = False
        self.message_handlers: List[callable] = []
        
    def add_message_handler(self, handler: callable):
        """Add a message handler function"""
        self.message_handlers.append(handler)
    
    def start_listening(self, port: int = 0, use_tunnel: bool = False) -> Tuple[bool, str]:
        """Start listening for incoming connections."""
        if self.listening:
            return False, "Already listening."

        self.listening = True

        if use_tunnel:
            # Tunnel mode: Start WebSocket server and tunnel
            tunnel_url = self.tunnel_manager.create_tunnel()
            if tunnel_url:
                self.server_port = self.tunnel_manager.ws_server_port
                return True, tunnel_url
            else:
                self.listening = False
                return False, "Failed to create tunnel."
        else:
            # Direct mode: Start TCP server
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.bind(('0.0.0.0', port))
                self.server_socket.listen(5)
                self.server_port = self.server_socket.getsockname()[1]

                listen_thread = threading.Thread(target=self._listen_for_connections, daemon=True)
                listen_thread.start()

                connection_info = f"localhost:{self.server_port}"
                return True, connection_info
            except Exception as e:
                self.listening = False
                return False, str(e)
    
    def stop_listening(self):
        """Stop listening for connections"""
        if not self.listening:
            return

        self.listening = False

        # If TCP server was running
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        # If tunnel was running
        self.tunnel_manager.close_tunnel()
        self.server_port = None
    
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

    async def _handle_incoming_websocket_connection(self, websocket, path: str):
        """Handle an incoming WebSocket connection from the tunnel."""
        peer_id = None
        try:
            # The first message is the handshake
            handshake_data = await websocket.recv()
            handshake = json.loads(handshake_data)

            peer_id = handshake.get('user_id')
            peer_username = handshake.get('username')

            if not all([peer_id, peer_username, handshake.get('public_key')]):
                await websocket.close(1002, "Handshake incomplete")
                return

            current_user = self.user_manager.get_current_user()
            if not current_user:
                await websocket.close(1008, "Server user not logged in")
                return

            # Send handshake response
            response = {
                'user_id': current_user.user_id,
                'username': current_user.username,
                'public_key': current_user.public_key,
                'status': 'accepted'
            }
            await websocket.send(json.dumps(response))

            # Create connection object
            connection = Connection(
                peer_id=peer_id,
                peer_username=peer_username,
                connection_type="tunnel-incoming",
                address=websocket.remote_address[0],
                port=websocket.remote_address[1],
                status="connected",
                established_at=datetime.now().isoformat(),
                websocket_obj=websocket
            )
            self.connections[peer_id] = connection
            self.contact_manager.update_contact_last_seen(peer_id)
            print(f"\n✅ Incoming tunnel connection from {peer_username} ({peer_id[:8]}...)")

            # Handle messages from this peer
            await self._handle_websocket_messages(peer_id, websocket)

        except (websockets.exceptions.ConnectionClosed, json.JSONDecodeError) as e:
            print(f"WebSocket connection closed with {peer_id or 'unknown peer'}: {e}")
        except Exception as e:
            print(f"Error handling incoming WebSocket connection: {e}")
        finally:
            if peer_id and peer_id in self.connections:
                del self.connections[peer_id]
            if not websocket.closed:
                await websocket.close()
    
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
            
            print(f"\nIncoming connection established with {peer_username} ({peer_id})")
            
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
            # Create socket connection
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)  # 10 second timeout
            
            if contact.connection_type == "direct" and contact.address:
                # Direct IP connection
                host, port = contact.address.split(':')
                client_socket.connect((host, int(port)))
            elif contact.connection_type == "tunnel" and contact.tunnel_url:
                # WebSocket tunnel connection
                return self._connect_via_websocket(peer_id, contact.tunnel_url)
            else:
                return False
            
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
            
            print(f"Successfully connected to {contact.username} ({peer_id})")
            return True
            
        except Exception as e:
            print(f"Failed to connect to peer: {e}")
            try:
                client_socket.close()
            except:
                pass
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
                # WebSocket connection
                asyncio.create_task(self._send_websocket_message(connection.websocket_obj, message_data))
                return True
            elif connection.socket_obj:
                # Socket connection
                connection.socket_obj.send(json.dumps(message_data).encode())
                return True
            else:
                return False
            
        except Exception as e:
            print(f"Failed to send message: {e}")
            return False
    
    async def _send_websocket_message(self, websocket, message_data):
        """Send message via WebSocket"""
        try:
            await websocket.send(json.dumps(message_data))
        except Exception as e:
            print(f"Failed to send WebSocket message: {e}")
    
    def disconnect_from_peer(self, peer_id: str):
        """Disconnect from a peer"""
        connection = self.connections.get(peer_id)
        if not connection:
            return

        connection.status = "disconnected"

        # Close TCP socket if it exists
        if connection.socket_obj:
            try:
                connection.socket_obj.close()
            except Exception as e:
                print(f"Error closing socket for {peer_id}: {e}")

        # Close WebSocket if it exists
        if connection.websocket_obj and not connection.websocket_obj.closed:
            loop = self.tunnel_manager.server_loop
            if loop and loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    connection.websocket_obj.close(), loop
                )
                try:
                    # Wait for the coroutine to finish
                    future.result(timeout=2)
                    print(f"WebSocket for {peer_id} closed.")
                except Exception as e:
                    print(f"Error closing WebSocket for {peer_id}: {e}")

        # Remove from active connections
        if peer_id in self.connections:
            del self.connections[peer_id]
    
    def get_active_connections(self) -> List[Connection]:
        """Get list of active connections"""
        return [conn for conn in self.connections.values() if conn.status == "connected"]
    
    def get_connection(self, peer_id: str) -> Optional[Connection]:
        """Get connection by peer ID"""
        return self.connections.get(peer_id)
    
    def _connect_via_websocket(self, peer_id: str, tunnel_url: str) -> bool:
        """Connect to a peer via a WebSocket tunnel."""
        try:
            # Convert http(s) URL to ws(s) URL
            if tunnel_url.startswith('https://'):
                ws_url = tunnel_url.replace('https://', 'wss://', 1)
            elif tunnel_url.startswith('http://'):
                ws_url = tunnel_url.replace('http://', 'ws://', 1)
            else:
                print(f"Invalid tunnel URL scheme: {tunnel_url}")
                return False

            # The WebSocket connection runs in a separate thread with its own event loop
            def ws_connect_thread():
                try:
                    # Each thread needs its own event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self._websocket_connect(peer_id, ws_url))
                except Exception as e:
                    print(f"WebSocket connection thread failed: {e}")

            ws_thread = threading.Thread(target=ws_connect_thread, daemon=True)
            ws_thread.start()

            # Give the connection a moment to establish
            import time
            time.sleep(3)

            return peer_id in self.connections and self.connections[peer_id].status == "connected"

        except Exception as e:
            print(f"Failed to initiate WebSocket connection: {e}")
            return False

    async def _websocket_connect(self, peer_id: str, ws_url: str):
        """Establishes and handles a client WebSocket connection."""
        print(f"Attempting to connect to WebSocket: {ws_url}")
        try:
            contact = self.contact_manager.get_contact(peer_id)
            current_user = self.user_manager.get_current_user()
            if not contact or not current_user:
                return

            # For wss://, create an SSL context that doesn't verify the cert,
            # as localtunnel uses self-signed certificates.
            ssl_context = None
            if ws_url.startswith('wss://'):
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

            async with websockets.connect(ws_url, ssl=ssl_context) as websocket:
                print(f"✅ WebSocket connection established to {ws_url}")
                await self._handle_websocket_connection(peer_id, websocket, contact, current_user)

        except (websockets.exceptions.InvalidURI, websockets.exceptions.InvalidHandshake) as e:
            print(f"❌ Failed to connect to {ws_url}: {e}")
            # If wss failed, try ws as a fallback
            if ws_url.startswith('wss://'):
                ws_fallback_url = ws_url.replace('wss://', 'ws://', 1)
                print(f"Attempting fallback connection to {ws_fallback_url}")
                await self._websocket_connect(peer_id, ws_fallback_url)
        except Exception as e:
            print(f"WebSocket connection error for {ws_url}: {e}")
    
    async def _handle_websocket_connection(self, peer_id: str, websocket, contact, current_user):
        """Handle the WebSocket connection after it's established"""
        try:
            # Send handshake
            handshake = {
                'user_id': current_user.user_id,
                'username': current_user.username,
                'public_key': current_user.public_key
            }
            await websocket.send(json.dumps(handshake))
            
            # Receive handshake response
            response_data = await websocket.recv()
            response = json.loads(response_data)
            
            if response.get('status') != 'accepted':
                return
            
            # Create connection object with WebSocket
            connection = Connection(
                peer_id=peer_id,
                peer_username=contact.username,
                connection_type="tunnel",
                address="websocket",
                port=0,
                status="connected",
                established_at=datetime.now().isoformat(),
                websocket_obj=websocket
            )
            
            self.connections[peer_id] = connection
            
            # Update contact last seen
            self.contact_manager.update_contact_last_seen(peer_id)
            
            print(f"Successfully connected to {contact.username} via tunnel")
            
            # Handle messages
            await self._handle_websocket_messages(peer_id, websocket)
            
        except Exception as e:
            print(f"WebSocket connection error: {e}")
    
    async def _handle_websocket_messages(self, peer_id: str, websocket):
        """Handle messages from WebSocket connection"""
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
