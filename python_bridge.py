#!/usr/bin/env python3
"""
Python bridge for WhisperLink Electron GUI
Handles communication between the Electron frontend and Python backend
"""

import sys
import json
import asyncio
import threading
from typing import Dict, Any, Optional
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from user_manager import UserManager
from contact_manager import ContactManager
from connection_manager import ConnectionManager
from models import User, Contact, Connection

class WhisperLinkBridge:
    def __init__(self):
        self.user_manager = UserManager()
        self.contact_manager = None  # Will be created when user logs in
        self.connection_manager = None  # Will be created when user logs in
        self.current_user: Optional[User] = None
    
    def _initialize_user_managers(self, user_id: str):
        """Initialize user-specific managers"""
        self.contact_manager = ContactManager(user_id=user_id)
        self.connection_manager = ConnectionManager(self.user_manager, self.contact_manager)
        
    def handle_command(self, command: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle commands from Electron frontend"""
        try:
            if command == 'ping':
                return {'success': True, 'message': 'pong'}
            elif command == 'register_user':
                return self._register_user(args)
            elif command == 'login_user':
                return self._login_user(args)
            elif command == 'logout_user':
                return self._logout_user()
            elif command == 'get_current_user':
                return self._get_current_user()
            elif command == 'add_contact':
                return self._add_contact(args)
            elif command == 'get_contacts':
                return self._get_contacts()
            elif command == 'remove_contact':
                return self._remove_contact(args)
            elif command == 'start_server':
                return self._start_server(args)
            elif command == 'stop_server':
                return self._stop_server(args)
            elif command == 'connect_to_peer':
                return self._connect_to_peer(args)
            elif command == 'send_message':
                return self._send_message(args)
            elif command == 'get_connections':
                return self._get_connections()
            elif command == 'disconnect_peer':
                return self._disconnect_peer(args)
            elif command == 'create_tunnel':
                return self._create_tunnel(args)
            elif command == 'close_tunnel':
                return self._close_tunnel(args)
            elif command == 'get_connection_info':
                return self._get_connection_info(args)
            else:
                return {'success': False, 'error': f'Unknown command: {command}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _register_user(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user"""
        username = args.get('username')
        password = args.get('password')
        
        if not username or not password:
            return {'success': False, 'error': 'Username and password required'}
        
        try:
            user_id = self.user_manager.register_user(username, password)
            
            # Automatically log in the new user and initialize their managers
            success = self.user_manager.login(username, password)
            if success:
                self.current_user = self.user_manager.get_current_user()
                self._initialize_user_managers(user_id)
                
                return {
                    'success': True, 
                    'user_id': user_id,
                    'user': {
                        'user_id': self.current_user.user_id,
                        'username': self.current_user.username,
                        'public_key': self.current_user.public_key,
                        'created_at': self.current_user.created_at,
                        'last_login': self.current_user.last_login
                    }
                }
            else:
                return {'success': True, 'user_id': user_id}
                
        except ValueError as e:
            return {'success': False, 'error': str(e)}
    
    def _login_user(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Login user"""
        username = args.get('username')
        password = args.get('password')
        
        if not username or not password:
            return {'success': False, 'error': 'Username and password required'}
        
        success = self.user_manager.login(username, password)
        if success:
            self.current_user = self.user_manager.get_current_user()
            # Initialize user-specific managers
            self._initialize_user_managers(self.current_user.user_id)
            
            return {
                'success': True, 
                'user': {
                    'user_id': self.current_user.user_id,
                    'username': self.current_user.username,
                    'public_key': self.current_user.public_key,
                    'created_at': self.current_user.created_at,
                    'last_login': self.current_user.last_login
                }
            }
        else:
            return {'success': False, 'error': 'Invalid credentials'}
    
    def _logout_user(self) -> Dict[str, Any]:
        """Logout current user"""
        self.user_manager.logout()
        self.current_user = None
        # Clear user-specific managers
        self.contact_manager = None
        self.connection_manager = None
        return {'success': True}
    
    def _get_current_user(self) -> Dict[str, Any]:
        """Get current user info"""
        if self.current_user:
            return {
                'success': True,
                'user': {
                    'user_id': self.current_user.user_id,
                    'username': self.current_user.username,
                    'public_key': self.current_user.public_key,
                    'created_at': self.current_user.created_at,
                    'last_login': self.current_user.last_login
                }
            }
        else:
            return {'success': False, 'error': 'No user logged in'}
    
    def _add_contact(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new contact"""
        if not self.current_user or not self.contact_manager:
            return {'success': False, 'error': 'Not logged in'}
        
        username = args.get('username')
        public_key = args.get('public_key')
        connection_type = args.get('connection_type', 'direct')
        address = args.get('address')
        tunnel_url = args.get('tunnel_url')
        
        if not username or not public_key:
            return {'success': False, 'error': 'Username and public key required'}
        
        try:
            # Generate a unique contact ID
            import uuid
            contact_id = str(uuid.uuid4()).replace('-', '')
            
            success = self.contact_manager.add_contact(
                contact_id,
                username,
                public_key,
                connection_type,
                address,
                tunnel_url
            )
            
            if success:
                return {'success': True, 'contact_id': contact_id}
            else:
                return {'success': False, 'error': 'Contact already exists'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_contacts(self) -> Dict[str, Any]:
        """Get all contacts for current user"""
        if not self.current_user or not self.contact_manager:
            return {'success': False, 'error': 'Not logged in'}
        
        contacts = self.contact_manager.list_contacts()
        contact_list = []
        
        for contact in contacts:
            contact_list.append({
                'user_id': contact.user_id,
                'username': contact.username,
                'public_key': contact.public_key,
                'connection_type': contact.connection_type,
                'address': contact.address,
                'tunnel_url': contact.tunnel_url,
                'added_at': contact.added_at,
                'last_seen': contact.last_seen
            })
        
        return {'success': True, 'contacts': contact_list}
    
    def _remove_contact(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a contact"""
        if not self.current_user or not self.contact_manager:
            return {'success': False, 'error': 'Not logged in'}
        
        contact_username = args.get('username')
        if not contact_username:
            return {'success': False, 'error': 'Contact username required'}
        
        try:
            success = self.contact_manager.remove_contact_by_username(contact_username)
            if success:
                return {'success': True}
            else:
                return {'success': False, 'error': 'Contact not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _start_server(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Start listening server"""
        if not self.current_user or not self.connection_manager:
            return {'success': False, 'error': 'Not logged in'}
        
        port = args.get('port', 9001)
        use_tunnel = args.get('use_tunnel', False)
        
        try:
            success, info = self.connection_manager.start_listening(port, use_tunnel)
            if success:
                return {
                    'success': True, 
                    'message': f'Server started on port {port}',
                    'connection_info': info,
                    'port': port
                }
            else:
                return {'success': False, 'error': info}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _stop_server(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Stop listening server"""
        if not self.current_user or not self.connection_manager:
            return {'success': False, 'error': 'Not logged in'}
        
        try:
            self.connection_manager.stop_listening()
            return {'success': True, 'message': 'Server stopped successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _connect_to_peer(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Connect to a peer"""
        if not self.current_user:
            return {'success': False, 'error': 'Not logged in'}
        
        peer_username = args.get('peer_username')
        host = args.get('host')
        port = args.get('port')
        ws_url = args.get('ws_url')
        
        if not peer_username:
            return {'success': False, 'error': 'Peer username required'}
        
        try:
            # This would be implemented with the actual connection manager
            return {'success': True, 'message': f'Connected to {peer_username}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_message(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to peer"""
        if not self.current_user:
            return {'success': False, 'error': 'Not logged in'}
        
        peer_username = args.get('peer_username')
        message = args.get('message')
        
        if not peer_username or not message:
            return {'success': False, 'error': 'Peer username and message required'}
        
        try:
            # This would be implemented with the actual connection manager
            return {'success': True, 'message': 'Message sent'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_connections(self) -> Dict[str, Any]:
        """Get active connections"""
        if not self.current_user:
            return {'success': False, 'error': 'Not logged in'}
        
        # This would return actual connections from connection manager
        return {'success': True, 'connections': []}
    
    def _disconnect_peer(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Disconnect from peer"""
        if not self.current_user:
            return {'success': False, 'error': 'Not logged in'}
        
        peer_username = args.get('peer_username')
        if not peer_username:
            return {'success': False, 'error': 'Peer username required'}
        
        try:
            # This would be implemented with the actual connection manager
            return {'success': True, 'message': f'Disconnected from {peer_username}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _create_tunnel(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a tunnel for the current server"""
        if not self.current_user or not self.connection_manager:
            return {'success': False, 'error': 'Not logged in'}
        
        port = args.get('port', self.connection_manager.server_port or 9001)
        
        try:
            if not self.connection_manager.server_port:
                return {'success': False, 'error': 'Server must be running to create tunnel'}
            
            tunnel_url = self.connection_manager.tunnel_manager.create_tunnel(port)
            if tunnel_url:
                return {
                    'success': True, 
                    'tunnel_url': tunnel_url,
                    'message': 'Tunnel created successfully'
                }
            else:
                return {'success': False, 'error': 'Failed to create tunnel'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _close_tunnel(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Close the active tunnel"""
        if not self.current_user or not self.connection_manager:
            return {'success': False, 'error': 'Not logged in'}
        
        port = args.get('port', self.connection_manager.server_port or 9001)
        
        try:
            self.connection_manager.tunnel_manager.close_tunnel(port)
            return {'success': True, 'message': 'Tunnel closed successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _get_connection_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get current connection information"""
        if not self.current_user or not self.connection_manager:
            return {'success': False, 'error': 'Not logged in'}
        
        port = args.get('port', self.connection_manager.server_port or 9001)
        
        try:
            if not self.connection_manager.server_port:
                return {'success': False, 'error': 'Server is not running'}
            
            # Get tunnel URL if exists
            tunnel_url = self.connection_manager.tunnel_manager.get_tunnel_url(port)
            direct_ip = f"localhost:{port}"
            
            return {
                'success': True,
                'direct_ip': direct_ip,
                'tunnel_url': tunnel_url,
                'port': port
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

def main():
    """Main bridge process"""
    bridge = WhisperLinkBridge()
    
    print("WhisperLink Python bridge started", flush=True)
    
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            
            try:
                data = json.loads(line.strip())
                command = data.get('command')
                args = data.get('args', {})
                
                response = bridge.handle_command(command, args)
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError:
                error_response = {'success': False, 'error': 'Invalid JSON'}
                print(json.dumps(error_response), flush=True)
            except Exception as e:
                error_response = {'success': False, 'error': f'Bridge error: {str(e)}'}
                print(json.dumps(error_response), flush=True)
                
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Bridge fatal error: {e}", file=sys.stderr)

if __name__ == '__main__':
    main()