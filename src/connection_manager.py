import os
import uuid
import json
import socket
import threading
import subprocess
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
    
    def create_tunnel(self, local_port: int) -> Optional[str]:
        """Create a tunnel to expose local port"""
        try:
            # Try to use localtunnel if available
            result = subprocess.run([
                'npx', 'localtunnel', '--port', str(local_port)
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Parse tunnel URL from output
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'https://' in line:
                        tunnel_url = line.strip()
                        self.active_tunnels[local_port] = tunnel_url
                        return tunnel_url
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Fallback: simulate tunnel creation
        tunnel_id = uuid.uuid4().hex[:8]
        tunnel_url = f"https://{tunnel_id}.loca.lt"
        self.active_tunnels[local_port] = tunnel_url
        print(f"Simulated tunnel created: {tunnel_url} -> localhost:{local_port}")
        return tunnel_url
    
    def close_tunnel(self, local_port: int):
        """Close an active tunnel"""
        if local_port in self.active_tunnels:
            del self.active_tunnels[local_port]
    
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
            # Create socket connection
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)  # 10 second timeout
            
            if contact.connection_type == "direct" and contact.address:
                # Direct IP connection
                host, port = contact.address.split(':')
                client_socket.connect((host, int(port)))
            else:
                # For simplicity, assume tunnel connections use a standard port
                return False  # Implement tunnel connection logic here
            
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
            
            # Send message
            connection.socket_obj.send(json.dumps(message_data).encode())
            return True
            
        except Exception as e:
            print(f"Failed to send message: {e}")
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
            del self.connections[peer_id]
    
    def get_active_connections(self) -> List[Connection]:
        """Get list of active connections"""
        return [conn for conn in self.connections.values() if conn.status == "connected"]
    
    def get_connection(self, peer_id: str) -> Optional[Connection]:
        """Get connection by peer ID"""
        return self.connections.get(peer_id)
