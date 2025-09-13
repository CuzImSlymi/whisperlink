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
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .models import Connection, Contact, User
from .user_manager import UserManager
from .contact_manager import ContactManager
from .crypto_manager import CryptoManager

class TunnelManager:
    """Manages tunnel connections for privacy"""
    
    def __init__(self):
        self.active_tunnels: Dict[int, str] = {}  # port -> tunnel_url
        self.ws_bridge_port = 9002  # WebSocket bridge port
        self.ws_bridge_running = False
        self.ws_bridge_server = None

    def create_tunnel(self, local_port: int) -> Optional[str]:
        """Create a tunnel to expose local port"""
        try:
            # Start WebSocket bridge if not running
            if not self.ws_bridge_running:
                print(f"Starting WebSocket bridge for port {local_port}")
                self._start_websocket_bridge(local_port)
                
            # Try to use localtunnel if available
            print(f"Attempting to create tunnel for port {self.ws_bridge_port}")
            result = subprocess.run([
                'npx', 'localtunnel', '--port', str(self.ws_bridge_port)
            ], capture_output=True, text=True, timeout=15)
            
            print(f"Localtunnel result: {result.returncode}")
            print(f"Localtunnel stdout: {result.stdout}")
            print(f"Localtunnel stderr: {result.stderr}")
            
            if result.returncode == 0:
                # Parse tunnel URL from output
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'https://' in line:
                        tunnel_url = line.strip()
                        self.active_tunnels[local_port] = tunnel_url
                        print(f"✅ Real tunnel created: {tunnel_url}")
                        return tunnel_url
                        
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"Localtunnel failed: {e}")
            
        # Fallback: simulate tunnel creation
        tunnel_id = uuid.uuid4().hex[:8]
        tunnel_url = f"https://{tunnel_id}.loca.lt"
        self.active_tunnels[local_port] = tunnel_url
        print(f"⚠️ Simulated tunnel created: {tunnel_url} -> localhost:{self.ws_bridge_port}")
        print("Note: This is a simulated tunnel. For real connections, install localtunnel:")
        print("npm install -g localtunnel")
        return tunnel_url

    def _start_websocket_bridge(self, tcp_port: int):
        """Start WebSocket bridge to forward to TCP server"""
        def run_bridge():
            async def handle_ws_client(websocket, path):
                try:
                    # Connect to the local TCP server
                    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    tcp_sock.connect(('127.0.0.1', tcp_port))
                    
                    async def tcp_to_ws():
                        try:
                            while True:
                                data = tcp_sock.recv(4096)
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
                                tcp_sock.sendall(message)
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
                    print(f"Bridge error: {e}")

            async def main():
                print(f"WebSocket bridge listening on 0.0.0.0:{self.ws_bridge_port} -> 127.0.0.1:{tcp_port}")
                self.ws_bridge_server = await websockets.serve(handle_ws_client, '0.0.0.0', self.ws_bridge_port)
                self.ws_bridge_running = True
                await self.ws_bridge_server.wait_closed()

            try:
                asyncio.run(main())
            except Exception as e:
                print(f"WebSocket bridge error: {e}")
                self.ws_bridge_running = False

        bridge_thread = threading.Thread(target=run_bridge, daemon=True)
        bridge_thread.start()
        
        # Wait a moment for bridge to start
        import time
        time.sleep(1)

    def close_tunnel(self, local_port: int):
        """Close an active tunnel"""
        if local_port in self.active_tunnels:
            del self.active_tunnels[local_port]
            
        if self.ws_bridge_server:
            self.ws_bridge_server.close()
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
                tunnel_url = self.tunnel_manager.create_tunnel(self.server_port)
                if tunnel_url:
                    connection_info = tunnel_url
                    
            return True, connection_info
            
        except Exception as e:
            return False, str(e)

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
            if contact.connection_type == "direct" and contact.address:
                # Direct IP connection
                return self._connect_direct(peer_id, contact, current_user)
            elif contact.connection_type == "tunnel" and contact.tunnel_url:
                # Tunnel connection
                return self._connect_via_tunnel(peer_id, contact, current_user)
            else:
                return False
                
        except Exception as e:
            print(f"Failed to connect to peer: {e}")
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
            
            print(f"Successfully connected to {contact.username} ({peer_id})")
            return True
            
        except Exception as e:
            print(f"Direct connection failed: {e}")
            try:
                client_socket.close()
            except:
                pass
            return False

    def _connect_via_tunnel(self, peer_id: str, contact: Contact, current_user: User) -> bool:
        """Connect to peer via tunnel"""
        try:
            # Use HTTP POST to tunnel endpoint to establish connection
            tunnel_url = contact.tunnel_url
            if not tunnel_url:
                return False
                
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
                    print(f"Async tunnel connection error: {e}")
                    result[0] = False
                finally:
                    loop.close()
            
            connect_thread = threading.Thread(target=run_async_connect, daemon=True)
            connect_thread.start()
            connect_thread.join(timeout=30)  # 30 second timeout
            
            return result[0]
            
        except Exception as e:
            print(f"Tunnel connection failed: {e}")
            return False

    async def _async_tunnel_connect(self, peer_id: str, contact: Contact, handshake: dict) -> bool:
        """Establish connection via HTTP tunnel using aiohttp"""
        try:
            tunnel_url = contact.tunnel_url.rstrip('/')
            
            # Create session with proper SSL handling
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                # First, try to establish WebSocket connection via tunnel
                try:
                    # Convert https to wss for WebSocket
                    ws_url = tunnel_url.replace('https://', 'wss://').replace('http://', 'ws://')
                    
                    print(f"Connecting to tunnel WebSocket: {ws_url}")
                    
                    # Create WebSocket connection
                    ws = await session.ws_connect(ws_url, ssl=False)
                    
                    # Send handshake
                    await ws.send_str(json.dumps(handshake))
                    
                    # Receive handshake response
                    response_msg = await ws.receive()
                    if response_msg.type == aiohttp.WSMsgType.TEXT:
                        response = json.loads(response_msg.data)
                        if response.get('status') == 'accepted':
                            # Create connection object
                            connection = Connection(
                                peer_id=peer_id,
                                peer_username=contact.username,
                                connection_type="tunnel",
                                address="tunnel",
                                port=0,
                                status="connected",
                                established_at=datetime.now().isoformat(),
                                websocket_obj=ws
                            )
                            self.connections[peer_id] = connection
                            
                            # Update contact last seen
                            self.contact_manager.update_contact_last_seen(peer_id)
                            
                            print(f"Successfully connected to {contact.username} via tunnel")
                            
                            # Handle messages in background task
                            asyncio.create_task(self._handle_websocket_messages(peer_id, ws))
                            
                            return True
                    
                    await ws.close()
                    return False
                    
                except Exception as e:
                    print(f"WebSocket tunnel connection failed: {e}")
                    
                    # Fallback: try HTTP connection
                    try:
                        # Send handshake via HTTP POST
                        async with session.post(f"{tunnel_url}/connect", json=handshake) as response:
                            if response.status == 200:
                                response_data = await response.json()
                                if response_data.get('status') == 'accepted':
                                    # Create a mock connection for HTTP-based tunnel
                                    connection = Connection(
                                        peer_id=peer_id,
                                        peer_username=contact.username,
                                        connection_type="tunnel_http",
                                        address="tunnel",
                                        port=0,
                                        status="connected",
                                        established_at=datetime.now().isoformat(),
                                        socket_obj=None  # Will use HTTP for messages
                                    )
                                    self.connections[peer_id] = connection
                                    
                                    print(f"Successfully connected to {contact.username} via HTTP tunnel")
                                    return True
                                    
                    except Exception as http_e:
                        print(f"HTTP tunnel connection also failed: {http_e}")
                        
                return False
                
        except Exception as e:
            print(f"Tunnel connection error: {e}")
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

    async def _handle_websocket_messages(self, peer_id: str, websocket):
        """Handle messages from WebSocket connection"""
        try:
            async for msg in websocket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        message_data = json.loads(msg.data)
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
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"WebSocket error: {websocket.exception()}")
                    break
                    
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
            elif connection.connection_type == "tunnel_http":
                # HTTP tunnel connection
                return self._send_http_message(peer_id, message_data)
            else:
                return False
                
        except Exception as e:
            print(f"Failed to send message: {e}")
            return False

    async def _send_websocket_message(self, websocket, message_data):
        """Send message via WebSocket"""
        try:
            await websocket.send_str(json.dumps(message_data))
        except Exception as e:
            print(f"Failed to send WebSocket message: {e}")

    def _send_http_message(self, peer_id: str, message_data: dict) -> bool:
        """Send message via HTTP tunnel"""
        try:
            contact = self.contact_manager.get_contact(peer_id)
            if not contact or not contact.tunnel_url:
                return False
                
            import requests
            response = requests.post(
                f"{contact.tunnel_url}/message",
                json=message_data,
                timeout=10
            )
            return response.status_code == 200
            
        except Exception as e:
            print(f"Failed to send HTTP message: {e}")
            return False

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
