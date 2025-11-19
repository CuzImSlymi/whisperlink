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
from datetime import datetime
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from user_manager import UserManager
from contact_manager import ContactManager
from connection_manager import ConnectionManager
from group_manager import GroupManager
from webrtc_manager import WebRTCManager
from models import User, Contact, Connection

class WhisperLinkBridge:
    def __init__(self):
        import sys
        # Increase max listeners to prevent memory leak warnings
        import os
        os.environ['UV_THREADPOOL_SIZE'] = '128'
        self.user_manager = UserManager()
        self.contact_manager = None  # Will be created when user logs in
        self.connection_manager = None  # Will be created when user logs in
        self.group_manager = None # Will be created when user logs in
        self.webrtc_manager = None  # Will be created when user logs in
        self.webrtc_loop = None  # Event loop for WebRTC
        self.current_user: Optional[User] = None
        self.pending_calls = []  # Store pending incoming calls
    
    def _initialize_user_managers(self, user_id: str):
        """Initialize user-specific managers"""
        self.contact_manager = ContactManager(user_id=user_id)
        self.group_manager = GroupManager(user_id=user_id)
        self.connection_manager = ConnectionManager(self.user_manager, self.contact_manager)
        # Add message handler to connection manager to handle incoming messages
        self.connection_manager.add_message_handler(self._handle_incoming_message)
        
        # Initialize WebRTC manager
        self.webrtc_manager = WebRTCManager(user_id, self._send_webrtc_signal_callback)
        self.webrtc_manager.add_call_handler('incoming_call', self._handle_incoming_call)
        self.webrtc_manager.add_call_handler('call_accepted', self._handle_call_accepted)
        self.webrtc_manager.add_call_handler('call_rejected', self._handle_call_rejected)
        self.webrtc_manager.add_call_handler('call_ended', self._handle_call_ended)
        
        # Add WebRTC signal handler to connection manager
        self.connection_manager.add_webrtc_signal_handler(self._handle_webrtc_signal)
        
        # Create event loop for WebRTC if needed
        import asyncio
        try:
            self.webrtc_loop = asyncio.get_event_loop()
        except RuntimeError:
            self.webrtc_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.webrtc_loop)
    
    def _handle_incoming_message(self, peer_id: str, peer_username: str, message: str, timestamp: str, 
                                  is_group: bool = False, group_id: str = None, group_name: str = None):
        """Handle incoming messages from peers"""
        # Store message for GUI to retrieve
        if not hasattr(self, 'pending_messages'):
            self.pending_messages = []
        
        message_data = {
            'peer_id': peer_id,
            'peer_username': peer_username,
            'message': message,
            'timestamp': timestamp,
            'type': 'group_received' if is_group else 'received',
            'is_group': is_group,
            'group_id': group_id,
            'group_name': group_name
        }
        
        self.pending_messages.append(message_data)
        if is_group:
            print(f"Received group message from {peer_username} in {group_name}: {message}", flush=True)
        else:
            print(f"Received message from {peer_username}: {message}", flush=True)
    
    def _send_webrtc_signal_callback(self, peer_id: str, signal_data: dict):
        """Callback for WebRTC manager to send signals via connection_manager"""
        if self.connection_manager:
            self.connection_manager.send_webrtc_signal(peer_id, signal_data)
    
    def _handle_webrtc_signal(self, peer_id: str, signal_data: dict):
        """Handle incoming WebRTC signal from peer"""
        if self.webrtc_manager and self.webrtc_loop:
            # Run the async handler in the event loop
            import asyncio
            asyncio.run_coroutine_threadsafe(
                self.webrtc_manager.handle_signal(signal_data),
                self.webrtc_loop
            )
    
    def _handle_incoming_call(self, call_id: str, from_peer: str):
        """Handle incoming call notification"""
        # Find peer's contact info
        contact = self.contact_manager.get_contact(from_peer) if self.contact_manager else None
        peer_username = contact.username if contact else "Unknown"
        
        call_data = {
            'call_id': call_id,
            'from_peer': from_peer,
            'from_username': peer_username,
            'type': 'incoming_call',
            'timestamp': datetime.now().isoformat()
        }
        self.pending_calls.append(call_data)
        print(f"Incoming call from {peer_username}", flush=True)
    
    def _handle_call_accepted(self, call_id: str, peer_id: str):
        """Handle call accepted event"""
        print(f"Call {call_id} accepted by {peer_id}", flush=True)
    
    def _handle_call_rejected(self, call_id: str, peer_id: str):
        """Handle call rejected event"""
        print(f"Call {call_id} rejected by {peer_id}", flush=True)
    
    def _handle_call_ended(self, call_id: str, peer_id: str):
        """Handle call ended event"""
        print(f"Call {call_id} ended with {peer_id}", flush=True)
        
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
            elif command == 'get_pending_messages':
                return self._get_pending_messages(args)
            elif command == 'create_group':
                return self._create_group(args)
            elif command == 'get_groups':
                return self._get_groups(args)
            elif command == 'get_group_details':
                return self._get_group_details(args)
            elif command == 'send_group_message':
                return self._send_group_message(args)
            elif command == 'add_group_member':
                return self._add_group_member(args)
            elif command == 'remove_group_member':
                return self._remove_group_member(args)
            elif command == 'leave_group':
                return self._leave_group(args)
            elif command == 'delete_group':
                return self._delete_group(args)
            elif command == 'start_voice_call':
                return self._start_voice_call(args)
            elif command == 'accept_voice_call':
                return self._accept_voice_call(args)
            elif command == 'reject_voice_call':
                return self._reject_voice_call(args)
            elif command == 'end_voice_call':
                return self._end_voice_call(args)
            elif command == 'get_pending_calls':
                return self._get_pending_calls(args)
            elif command == 'get_active_calls':
                return self._get_active_calls()
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
        self.group_manager = None
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
        if not self.current_user or not self.connection_manager:
            return {'success': False, 'error': 'Not logged in'}
        
        peer_username = args.get('peer_username')
        
        if not peer_username:
            return {'success': False, 'error': 'Peer username required'}
        
        try:
            # Find the contact by username to get their user_id
            contacts = self.contact_manager.list_contacts()
            peer_contact = None
            for contact in contacts:
                if contact.username == peer_username:
                    peer_contact = contact
                    break
            
            if not peer_contact:
                return {'success': False, 'error': f'Contact {peer_username} not found'}
            
            # Use connection manager to connect
            success = self.connection_manager.connect_to_peer(peer_contact.user_id)
            
            if success:
                return {'success': True, 'message': f'Connected to {peer_username}'}
            else:
                return {'success': False, 'error': f'Failed to connect to {peer_username}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_message(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to peer"""
        if not self.current_user or not self.connection_manager:
            return {'success': False, 'error': 'Not logged in'}
        
        peer_username = args.get('peer_username')
        message = args.get('message')
        
        if not peer_username or not message:
            return {'success': False, 'error': 'Peer username and message required'}
        
        try:
            # Find the contact by username to get their user_id
            contacts = self.contact_manager.list_contacts()
            peer_contact = None
            for contact in contacts:
                if contact.username == peer_username:
                    peer_contact = contact
                    break
            
            if not peer_contact:
                return {'success': False, 'error': f'Contact {peer_username} not found'}
            
            # Use connection manager to send message
            success = self.connection_manager.send_message(peer_contact.user_id, message)
            
            if success:
                return {'success': True, 'message': 'Message sent'}
            else:
                return {'success': False, 'error': 'Failed to send message - not connected to peer'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_connections(self) -> Dict[str, Any]:
        """Get active connections"""
        if not self.current_user or not self.connection_manager:
            return {'success': False, 'error': 'Not logged in'}
        
        try:
            connections = self.connection_manager.get_active_connections()
            connection_list = []
            
            for conn in connections:
                connection_list.append({
                    'peer_id': conn.peer_id,
                    'peer_username': conn.peer_username,
                    'connection_type': conn.connection_type,
                    'status': conn.status,
                    'address': conn.address,
                    'port': conn.port,
                    'established_at': conn.established_at
                })
            
            return {'success': True, 'connections': connection_list}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _disconnect_peer(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Disconnect from peer"""
        if not self.current_user or not self.connection_manager:
            return {'success': False, 'error': 'Not logged in'}
        
        peer_username = args.get('peer_username')
        if not peer_username:
            return {'success': False, 'error': 'Peer username required'}
        
        try:
            # Find the contact by username to get their user_id
            contacts = self.contact_manager.list_contacts()
            peer_contact = None
            for contact in contacts:
                if contact.username == peer_username:
                    peer_contact = contact
                    break
            
            if not peer_contact:
                return {'success': False, 'error': f'Contact {peer_username} not found'}
            
            # Use connection manager to disconnect
            self.connection_manager.disconnect_from_peer(peer_contact.user_id)
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

    def _get_pending_messages(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get and clear pending messages"""
        if not self.current_user:
            return {'success': False, 'error': 'Not logged in'}
        
        try:
            if not hasattr(self, 'pending_messages'):
                self.pending_messages = []
            
            messages = self.pending_messages.copy()
            self.pending_messages.clear()  # Clear after retrieving
            
            return {'success': True, 'messages': messages}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _create_group(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new group"""
        if not self.current_user or not self.group_manager:
            return {'success': False, 'error': 'Not logged in'}
        
        name = args.get('name')
        members = args.get('members', [])
        description = args.get('description')
        
        if not name:
            return {'success': False, 'error': 'Group name required'}
            
        try:
            group = self.group_manager.create_group(name, members, description)
            return {
                'success': True,
                'group': {
                    'group_id': group.group_id,
                    'name': group.name,
                    'members': group.members,
                    'created_at': group.created_at,
                    'admin_id': group.admin_id,
                    'description': group.description
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _get_groups(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get all groups"""
        if not self.current_user or not self.group_manager:
            return {'success': False, 'error': 'Not logged in'}
            
        try:
            groups = self.group_manager.list_groups()
            group_list = []
            
            for group in groups:
                group_list.append({
                    'group_id': group.group_id,
                    'name': group.name,
                    'members': group.members,
                    'created_at': group.created_at,
                    'admin_id': group.admin_id,
                    'description': group.description
                })
                
            return {'success': True, 'groups': group_list}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _get_group_details(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get group details"""
        if not self.current_user or not self.group_manager:
            return {'success': False, 'error': 'Not logged in'}
            
        group_id = args.get('group_id')
        if not group_id:
            return {'success': False, 'error': 'Group ID required'}
            
        try:
            group = self.group_manager.get_group(group_id)
            if group:
                return {
                    'success': True,
                    'group': {
                        'group_id': group.group_id,
                        'name': group.name,
                        'members': group.members,
                        'created_at': group.created_at,
                        'admin_id': group.admin_id,
                        'description': group.description
                    }
                }
            else:
                return {'success': False, 'error': 'Group not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _send_group_message(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to a group"""
        if not self.current_user or not self.connection_manager or not self.group_manager:
            return {'success': False, 'error': 'Not logged in'}
            
        group_id = args.get('group_id')
        message = args.get('message')
        
        if not group_id or not message:
            return {'success': False, 'error': 'Group ID and message required'}
            
        try:
            group = self.group_manager.get_group(group_id)
            if not group:
                return {'success': False, 'error': 'Group not found'}
                
            # Send message to all group members
            results = self.connection_manager.send_group_message(
                group.members, 
                message, 
                group_id=group.group_id,
                group_name=group.name
            )
            
            # Count successful deliveries
            successful = sum(1 for success in results.values() if success)
            total = len([m for m in group.members if m != self.current_user.user_id])
            
            return {
                'success': True,
                'delivered': successful,
                'total': total,
                'results': results
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _add_group_member(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Add a member to a group"""
        if not self.current_user or not self.group_manager:
            return {'success': False, 'error': 'Not logged in'}
            
        group_id = args.get('group_id')
        member_id = args.get('member_id')
        
        if not group_id or not member_id:
            return {'success': False, 'error': 'Group ID and member ID required'}
            
        try:
            group = self.group_manager.get_group(group_id)
            if not group:
                return {'success': False, 'error': 'Group not found'}
                
            # Check if current user is admin
            if group.admin_id != self.current_user.user_id:
                return {'success': False, 'error': 'Only group admin can add members'}
                
            success = self.group_manager.add_member(group_id, member_id)
            if success:
                return {'success': True}
            else:
                return {'success': False, 'error': 'Member already in group or failed to add'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _remove_group_member(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a member from a group"""
        if not self.current_user or not self.group_manager:
            return {'success': False, 'error': 'Not logged in'}
            
        group_id = args.get('group_id')
        member_id = args.get('member_id')
        
        if not group_id or not member_id:
            return {'success': False, 'error': 'Group ID and member ID required'}
            
        try:
            group = self.group_manager.get_group(group_id)
            if not group:
                return {'success': False, 'error': 'Group not found'}
                
            # Check if current user is admin
            if group.admin_id != self.current_user.user_id:
                return {'success': False, 'error': 'Only group admin can remove members'}
                
            success = self.group_manager.remove_member(group_id, member_id)
            if success:
                return {'success': True}
            else:
                return {'success': False, 'error': 'Member not in group or failed to remove'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _leave_group(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Leave a group"""
        if not self.current_user or not self.group_manager:
            return {'success': False, 'error': 'Not logged in'}
            
        group_id = args.get('group_id')
        
        if not group_id:
            return {'success': False, 'error': 'Group ID required'}
            
        try:
            group = self.group_manager.get_group(group_id)
            if not group:
                return {'success': False, 'error': 'Group not found'}
                
            # If admin is leaving, either transfer admin or delete group
            if group.admin_id == self.current_user.user_id:
                # Delete the group if admin leaves
                self.group_manager.delete_group(group_id)
                return {'success': True, 'message': 'Group deleted (you were the admin)'}
            else:
                success = self.group_manager.remove_member(group_id, self.current_user.user_id)
                if success:
                    return {'success': True}
                else:
                    return {'success': False, 'error': 'Failed to leave group'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _delete_group(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a group"""
        if not self.current_user or not self.group_manager:
            return {'success': False, 'error': 'Not logged in'}
            
        group_id = args.get('group_id')
        
        if not group_id:
            return {'success': False, 'error': 'Group ID required'}
            
        try:
            group = self.group_manager.get_group(group_id)
            if not group:
                return {'success': False, 'error': 'Group not found'}
                
            # Check if current user is admin
            if group.admin_id != self.current_user.user_id:
                return {'success': False, 'error': 'Only group admin can delete the group'}
                
            success = self.group_manager.delete_group(group_id)
            if success:
                return {'success': True}
            else:
                return {'success': False, 'error': 'Failed to delete group'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _start_voice_call(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Start a voice call with a peer"""
        if not self.current_user or not self.webrtc_manager or not self.webrtc_loop:
            return {'success': False, 'error': 'Not logged in or WebRTC not initialized'}
            
        peer_id = args.get('peer_id')
        if not peer_id:
            return {'success': False, 'error': 'Peer ID required'}
            
        try:
            # Generate unique call ID
            import uuid
            call_id = str(uuid.uuid4())
            
            # Start call asynchronously
            future = asyncio.run_coroutine_threadsafe(
                self.webrtc_manager.start_call(peer_id, call_id),
                self.webrtc_loop
            )
            success = future.result(timeout=10)
            
            if success:
                return {'success': True, 'call_id': call_id}
            else:
                return {'success': False, 'error': 'Failed to start call'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _accept_voice_call(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Accept an incoming voice call"""
        if not self.current_user or not self.webrtc_manager or not self.webrtc_loop:
            return {'success': False, 'error': 'Not logged in or WebRTC not initialized'}
            
        call_id = args.get('call_id')
        if not call_id:
            return {'success': False, 'error': 'Call ID required'}
            
        try:
            # Accept call asynchronously
            future = asyncio.run_coroutine_threadsafe(
                self.webrtc_manager.accept_call(call_id),
                self.webrtc_loop
            )
            success = future.result(timeout=10)
            
            if success:
                # Remove from pending calls
                self.pending_calls = [c for c in self.pending_calls if c['call_id'] != call_id]
                return {'success': True}
            else:
                return {'success': False, 'error': 'Failed to accept call'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _reject_voice_call(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Reject an incoming voice call"""
        if not self.current_user or not self.webrtc_manager or not self.webrtc_loop:
            return {'success': False, 'error': 'Not logged in or WebRTC not initialized'}
            
        call_id = args.get('call_id')
        if not call_id:
            return {'success': False, 'error': 'Call ID required'}
            
        try:
            # Reject call asynchronously
            future = asyncio.run_coroutine_threadsafe(
                self.webrtc_manager.reject_call(call_id),
                self.webrtc_loop
            )
            success = future.result(timeout=10)
            
            # Remove from pending calls
            self.pending_calls = [c for c in self.pending_calls if c['call_id'] != call_id]
            
            if success:
                return {'success': True}
            else:
                return {'success': False, 'error': 'Failed to reject call'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _end_voice_call(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """End an active voice call"""
        if not self.current_user or not self.webrtc_manager or not self.webrtc_loop:
            return {'success': False, 'error': 'Not logged in or WebRTC not initialized'}
            
        call_id = args.get('call_id')
        if not call_id:
            return {'success': False, 'error': 'Call ID required'}
            
        try:
            # End call asynchronously
            future = asyncio.run_coroutine_threadsafe(
                self.webrtc_manager.end_call(call_id),
                self.webrtc_loop
            )
            success = future.result(timeout=10)
            
            if success:
                return {'success': True}
            else:
                return {'success': False, 'error': 'Failed to end call'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _get_pending_calls(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get pending incoming calls"""
        try:
            calls = self.pending_calls.copy()
            # Clear pending calls after retrieving
            self.pending_calls = []
            return {'success': True, 'calls': calls}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _get_active_calls(self) -> Dict[str, Any]:
        """Get all active calls"""
        if not self.webrtc_manager:
            return {'success': False, 'error': 'WebRTC not initialized'}
            
        try:
            calls = self.webrtc_manager.get_all_active_calls()
            calls_data = [
                {
                    'call_id': call.call_id,
                    'peer_id': call.callee_id if call.direction == 'outgoing' else call.caller_id,
                    'direction': call.direction,
                    'status': call.status,
                    'created_at': call.created_at,
                    'started_at': call.started_at
                }
                for call in calls
            ]
            return {'success': True, 'calls': calls_data}
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