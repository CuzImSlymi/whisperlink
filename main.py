#!/usr/bin/env python3
"""
WhisperLink - Secure P2P Encrypted Messenger MVP
Created for maximum privacy and encryption
Cross-platform P2P messaging with end-to-end encryption
"""

import os
import sys
import argparse
import getpass
import socket # For _get_local_ip
from typing import List, Tuple
from datetime import datetime

from src.models import User, Contact, Connection
from src.crypto_manager import CryptoManager, ENCRYPTION_AVAILABLE
from src.user_manager import UserManager
from src.contact_manager import ContactManager
from src.connection_manager import ConnectionManager

class WhisperLinkCLI:
    """Main CLI interface for WhisperLink"""
    
    def __init__(self):
        self.user_manager = UserManager()
        self.contact_manager = ContactManager()
        self.connection_manager = ConnectionManager(self.user_manager, self.contact_manager)
        self.running = True
        
        # Add message handler
        self.connection_manager.add_message_handler(self._handle_received_message)
        
        # Chat history for current session
        self.chat_history: List[Tuple[str, str, str, str]] = []  # (peer_id, username, message, timestamp)
    
    def _handle_received_message(self, peer_id: str, username: str, message: str, timestamp: str):
        """Handle received messages"""
        self.chat_history.append((peer_id, username, message, timestamp))
        print(f"\n💬 Message from {username}: {message}")
        print("Press Enter to continue...")
    
    def start(self):
        """Start the WhisperLink CLI"""
        print("=" * 50)
        print("🔒 WhisperLink - Secure P2P Messenger")
        print("=" * 50)
        print()
        
        if not ENCRYPTION_AVAILABLE:
            print("⚠️  WARNING: PyNaCl not available. Using mock encryption for demo.")
            print("   Install PyNaCl for real security: pip install PyNaCl")
            print()
        
        # Check if user is logged in
        if not self._login_flow():
            return
        
        # Main menu loop
        while self.running:
            try:
                self._show_main_menu()
                choice = input("Enter your choice: ").strip()
                self._handle_menu_choice(choice)
            except KeyboardInterrupt:
                print("\n\nShutting down WhisperLink...")
                self._cleanup()
                break
            except Exception as e:
                print(f"Error: {e}")
                input("Press Enter to continue...")
    
    def _login_flow(self) -> bool:
        """Handle user login/registration"""
        while True:
            print("1. Login")
            print("2. Register new account")  
            print("3. Exit")
            
            choice = input("Choose option (1-3): ").strip()
            
            if choice == "1":
                if self._login():
                    return True
            elif choice == "2":
                if self._register():
                    return True
            elif choice == "3":
                return False
            else:
                print("Invalid choice. Please try again.\n")
    
    def _login(self) -> bool:
        """Login user"""
        print("\n--- Login ---")
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        
        if self.user_manager.login(username, password):
            user = self.user_manager.get_current_user()
            print(f"✅ Welcome back, {user.username}!")
            print(f"Your User ID: {user.user_id}")
            print()
            return True
        else:
            print("❌ Invalid username or password.\n")
            return False
    
    def _register(self) -> bool:
        """Register new user"""
        print("\n--- Registration ---")
        username = input("Choose username: ").strip()
        if not username:
            print("Username cannot be empty.\n")
            return False
        
        password = getpass.getpass("Choose password: ")
        password_confirm = getpass.getpass("Confirm password: ")
        
        if password != password_confirm:
            print("❌ Passwords don't match.\n")
            return False
        
        if len(password) < 8:
            print("❌ Password must be at least 8 characters long.\n")
            return False
        
        try:
            user_id = self.user_manager.register_user(username, password)
            print(f"✅ Account created successfully!")
            print(f"Your User ID: {user_id}")
            print("Please log in with your credentials.")
            print()
            return False  # Make them log in after registration
        except ValueError as e:
            print(f"❌ Registration failed: {e}\n")
            return False
    
    def _show_main_menu(self):
        """Display the main menu"""
        user = self.user_manager.get_current_user()
        active_connections = self.connection_manager.get_active_connections()
        
        print("\n" + "=" * 50)
        print(f"User: {user.username} | User ID: {user.user_id}")
        print(f"Active Connections: {len(active_connections)}")
        if self.connection_manager.listening:
            print(f"Listening on: localhost:{self.connection_manager.server_port}")
        print("=" * 50)
        print()
        print("MAIN MENU:")
        print("1. Start listening for connections")
        print("2. Connect to a peer")
        print("3. Manage contacts")
        print("4. View connections")
        print("5. Chat with connected peer")
        print("6. Export my public info")
        print("7. Logout")
        print("8. Exit")
        print()
    
    def _handle_menu_choice(self, choice: str):
        """Handle menu choice"""
        if choice == "1":
            self._start_listening_menu()
        elif choice == "2":
            self._connect_to_peer_menu()
        elif choice == "3":
            self._manage_contacts_menu()
        elif choice == "4":
            self._view_connections_menu()
        elif choice == "5":
            self._chat_menu()
        elif choice == "6":
            self._export_public_info()
        elif choice == "7":
            self._logout()
        elif choice == "8":
            self._exit()
        else:
            print("Invalid choice. Please try again.")
    
    def _start_listening_menu(self):
        """Start listening for connections menu"""
        print("\n--- Start Listening for Connections ---")
        
        if self.connection_manager.listening:
            print("Already listening for connections.")
            choice = input("Stop listening? (y/n): ").lower()
            if choice == 'y':
                self.connection_manager.stop_listening()
                print("✅ Stopped listening for connections.")
            return
        
        print("1. Listen with direct IP (faster, IP visible)")
        print("2. Listen with tunnel (slower, IP hidden)")
        print("3. Cancel")
        
        choice = input("Choose option (1-3): ").strip()
        
        if choice == "1":
            success, info = self.connection_manager.start_listening(use_tunnel=False)
            if success:
                print(f"✅ Listening for connections on: {info}")
                print("Share this address with peers to connect directly.")
            else:
                print(f"❌ Failed to start listening: {info}")
        
        elif choice == "2":
            print("Starting tunnel... (this may take a moment)")
            success, info = self.connection_manager.start_listening(use_tunnel=True)
            if success:
                print(f"✅ Listening for connections via tunnel: {info}")
                print("Share this URL with peers to connect securely.")
            else:
                print(f"❌ Failed to start listening: {info}")
        
        input("\nPress Enter to continue...")
    
    def _connect_to_peer_menu(self):
        """Connect to peer menu"""
        print("\n--- Connect to a Peer ---")
        
        # Show available contacts
        contacts = self.contact_manager.list_contacts()
        if contacts:
            print("Available contacts:")
            for i, contact in enumerate(contacts, 1):
                status = "🟢 Online" if contact.user_id in self.connection_manager.connections else "⚫ Offline"
                print(f"{i}. {contact.username} ({contact.user_id}) - {status}")
            print(f"{len(contacts) + 1}. Connect to new peer")
            print(f"{len(contacts) + 2}. Cancel")
            
            choice = input(f"Choose option (1-{len(contacts) + 2}): ").strip()
            
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(contacts):
                    contact = contacts[choice_num - 1]
                    if contact.user_id in self.connection_manager.connections:
                        print("Already connected to this peer.")
                    else:
                        print(f"Connecting to {contact.username}...")
                        if self.connection_manager.connect_to_peer(contact.user_id):
                            print("✅ Successfully connected!")
                        else:
                            print("❌ Failed to connect.")
                elif choice_num == len(contacts) + 1:
                    self._connect_to_new_peer()
            except ValueError:
                print("Invalid choice.")
        else:
            print("No contacts available.")
            self._connect_to_new_peer()
        
        input("\nPress Enter to continue...")
    
    def _connect_to_new_peer(self):
        """Connect to a new peer not in contacts"""
        print("\n--- Connect to New Peer ---")
        peer_id = input("Enter peer's User ID: ").strip()
        username = input("Enter peer's username: ").strip()
        public_key = input("Enter peer's public key: ").strip()
        
        print("Connection type:")
        print("1. Direct IP connection")
        print("2. Tunnel connection") 
        
        conn_choice = input("Choose (1-2): ").strip()
        
        if conn_choice == "1":
            address = input("Enter IP address (host:port): ").strip()
            
            if self.contact_manager.add_contact(peer_id, username, public_key, "direct", address):
                print("Contact added.")
                
                print("Connecting...")
                if self.connection_manager.connect_to_peer(peer_id):
                    print("✅ Successfully connected!")
                else:
                    print("❌ Failed to connect.")
            else:
                print("Contact already exists.")
        
        elif conn_choice == "2":
            tunnel_url = input("Enter tunnel URL: ").strip()
            
            if self.contact_manager.add_contact(peer_id, username, public_key, "tunnel", tunnel_url=tunnel_url):
                print("Contact added.")
                print("Connecting via tunnel...")
                if self.connection_manager.connect_to_peer(peer_id):
                    print("✅ Successfully connected via tunnel!")
                else:
                    print("❌ Failed to connect via tunnel.")
            else:
                print("Contact already exists.")
    
    def _manage_contacts_menu(self):
        """Manage contacts menu"""
        while True:
            print("\n--- Manage Contacts ---")
            contacts = self.contact_manager.list_contacts()
            
            if contacts:
                print("Your contacts:")
                for i, contact in enumerate(contacts, 1):
                    conn_status = "🟢 Connected" if contact.user_id in self.connection_manager.connections else "⚫ Not connected"
                    last_seen = contact.last_seen or "Never"
                    print(f"{i}. {contact.username} ({contact.user_id[:8]}...)")
                    print(f"   Type: {contact.connection_type} | {conn_status} | Last seen: {last_seen}")
                print()
            else:
                print("No contacts found.")
            
            print("Options:")
            print("1. Add new contact")
            print("2. Remove contact") 
            print("3. View contact details")
            print("4. Back to main menu")
            
            choice = input("Choose option (1-4): ").strip()
            
            if choice == "1":
                self._add_contact_menu()
            elif choice == "2":
                self._remove_contact_menu()
            elif choice == "3":
                self._view_contact_details_menu()
            elif choice == "4":
                break
            else:
                print("Invalid choice.")
    
    def _add_contact_menu(self):
        """Add new contact"""
        print("\n--- Add New Contact ---")
        
        user_id = input("User ID: ").strip()
        username = input("Username: ").strip()
        public_key = input("Public Key: ").strip()
        
        print("Connection type:")
        print("1. Direct IP")
        print("2. Tunnel")
        
        conn_choice = input("Choose (1-2): ").strip()
        
        if conn_choice == "1":
            address = input("IP Address (host:port): ").strip()
            if self.contact_manager.add_contact(user_id, username, public_key, "direct", address):
                print("✅ Contact added successfully!")
            else:
                print("❌ Contact already exists or invalid data.")
        
        elif conn_choice == "2":
            tunnel_url = input("Tunnel URL: ").strip()
            if self.contact_manager.add_contact(user_id, username, public_key, "tunnel", tunnel_url=tunnel_url):
                print("✅ Contact added successfully!")
            else:
                print("❌ Contact already exists or invalid data.")
    
    def _remove_contact_menu(self):
        """Remove contact"""
        contacts = self.contact_manager.list_contacts()
        if not contacts:
            print("No contacts to remove.")
            return
        
        print("\n--- Remove Contact ---")
        for i, contact in enumerate(contacts, 1):
            print(f"{i}. {contact.username} ({contact.user_id[:8]}...)")
        
        try:
            choice = int(input(f"Choose contact to remove (1-{len(contacts)}): ").strip())
            if 1 <= choice <= len(contacts):
                contact = contacts[choice - 1]
                confirm = input(f"Remove {contact.username}? (y/n): ").lower()
                if confirm == 'y':
                    if self.contact_manager.remove_contact(contact.user_id):
                        print("✅ Contact removed.")
                    else:
                        print("❌ Failed to remove contact.")
        except ValueError:
            print("Invalid choice.")
    
    def _view_contact_details_menu(self):
        """View contact details"""
        contacts = self.contact_manager.list_contacts()
        if not contacts:
            print("No contacts available.")
            return
        
        print("\n--- Contact Details ---")
        for i, contact in enumerate(contacts, 1):
            print(f"{i}. {contact.username}")
        
        try:
            choice = int(input(f"Choose contact (1-{len(contacts)}): ").strip())
            if 1 <= choice <= len(contacts):
                contact = contacts[choice - 1]
                
                print(f"\n--- {contact.username} ---")
                print(f"User ID: {contact.user_id}")
                print(f"Public Key: {contact.public_key}")
                print(f"Connection Type: {contact.connection_type}")
                print(f"Address: {contact.address or 'N/A'}")
                print(f"Tunnel URL: {contact.tunnel_url or 'N/A'}")
                print(f"Added: {contact.added_at}")
                print(f"Last Seen: {contact.last_seen or 'Never'}")
                
                conn_status = "🟢 Connected" if contact.user_id in self.connection_manager.connections else "⚫ Not connected"
                print(f"Status: {conn_status}")
                
        except ValueError:
            print("Invalid choice.")
        
        input("\nPress Enter to continue...")
    
    def _view_connections_menu(self):
        """View active connections"""
        print("\n--- Active Connections ---")
        
        connections = self.connection_manager.get_active_connections()
        
        if not connections:
            print("No active connections.")
        else:
            print(f"Found {len(connections)} active connection(s):")
            print()
            
            for i, conn in enumerate(connections, 1):
                print(f"{i}. {conn.peer_username} ({conn.peer_id[:8]}...)")
                print(f"   Type: {conn.connection_type}")
                print(f"   Address: {conn.address}:{conn.port}")
                print(f"   Status: {conn.status}")
                print(f"   Connected: {conn.established_at}")
                print()
        
        if connections:
            print("Options:")
            print("1. Disconnect from peer")
            print("2. Back to main menu")
            
            choice = input("Choose option (1-2): ").strip()
            
            if choice == "1":
                try:
                    peer_choice = int(input(f"Choose peer to disconnect (1-{len(connections)}): ").strip())
                    if 1 <= peer_choice <= len(connections):
                        conn = connections[peer_choice - 1]
                        self.connection_manager.disconnect_from_peer(conn.peer_id)
                        print(f"✅ Disconnected from {conn.peer_username}")
                except ValueError:
                    print("Invalid choice.")
        
        input("\nPress Enter to continue...")
    
    def _chat_menu(self):
        """Chat with connected peers"""
        print("\n--- Chat with Connected Peer ---")
        
        connections = self.connection_manager.get_active_connections()
        
        if not connections:
            print("No active connections. Connect to a peer first.")
            input("Press Enter to continue...")
            return
        
        print("Select peer to chat with:")
        for i, conn in enumerate(connections, 1):
            print(f"{i}. {conn.peer_username} ({conn.peer_id[:8]}...)")
        
        try:
            choice = int(input(f"Choose peer (1-{len(connections)}): ").strip())
            if 1 <= choice <= len(connections):
                conn = connections[choice - 1]
                self._start_chat_session(conn.peer_id, conn.peer_username)
        except ValueError:
            print("Invalid choice.")
            input("Press Enter to continue...")
    
    def _start_chat_session(self, peer_id: str, peer_username: str):
        """Start a chat session with a peer"""
        print(f"\n--- Chat with {peer_username} ---")
        print("Type 'exit' to return to main menu")
        print("Type 'history' to view recent messages")
        print("-" * 40)
        
        # Show recent chat history for this peer
        recent_messages = [(pid, username, msg, ts) for pid, username, msg, ts in self.chat_history if pid == peer_id]
        if recent_messages:
            print("Recent messages:")
            for _, username, message, timestamp in recent_messages[-5:]:
                time_str = datetime.fromisoformat(timestamp).strftime("%H:%M:%S")
                print(f"[{time_str}] {username}: {message}")
            print("-" * 40)
        
        while True:
            try:
                message = input("You: ").strip()
                
                if message.lower() == 'exit':
                    break
                elif message.lower() == 'history':
                    self._show_chat_history(peer_id)
                    continue
                elif not message:
                    continue
                
                # Send message
                if self.connection_manager.send_message(peer_id, message):
                    # Add to local chat history
                    self.chat_history.append((
                        peer_id,
                        "You",
                        message,
                        datetime.now().isoformat()
                    ))
                else:
                    print("❌ Failed to send message. Connection may be lost.")
                    
            except KeyboardInterrupt:
                break
        
        print("Returning to main menu...")
    
    def _show_chat_history(self, peer_id: str):
        """Show chat history for a specific peer"""
        messages = [(pid, username, msg, ts) for pid, username, msg, ts in self.chat_history if pid == peer_id]
        
        if not messages:
            print("No chat history available.")
            return
        
        print("\n--- Chat History ---")
        for _, username, message, timestamp in messages:
            time_str = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{time_str}] {username}: {message}")
        print("-" * 40)
    
    def _export_public_info(self):
        """Export user's public information"""
        user = self.user_manager.get_current_user()
        if not user:
            return
        
        print("\n--- Export My Public Info ---")
        print("Share this information with others to allow them to add you as a contact:")
        print()
        print("-" * 50)
        print(f"Username: {user.username}")
        print(f"User ID: {user.user_id}")
        print(f"Public Key: {user.public_key}")
        
        # Show connection information if listening
        if self.connection_manager.listening:
            if self.connection_manager.server_port:
                local_ip = self._get_local_ip()
                print(f"Direct Connection: {local_ip}:{self.connection_manager.server_port}")
            
            # Show tunnel URL if available
            tunnel_url = self.connection_manager.tunnel_manager.get_tunnel_url(self.connection_manager.server_port or 0)
            if tunnel_url:
                print(f"Tunnel Connection: {tunnel_url}")
        else:
            print("Connection Info: Not currently listening for connections")
        
        print("-" * 50)
        print()
        
        # Option to save to file
        save_choice = input("Save to file? (y/n): ").lower()
        if save_choice == 'y':
            filename = f"whisperlink_{user.username}_public.txt"
            try:
                with open(filename, 'w') as f:
                    f.write(f"WhisperLink Public Information\n")
                    f.write(f"Username: {user.username}\n")
                    f.write(f"User ID: {user.user_id}\n")
                    f.write(f"Public Key: {user.public_key}\n")
                    f.write(f"Generated: {datetime.now().isoformat()}\n")
                
                print(f"✅ Public information saved to {filename}")
            except Exception as e:
                print(f"❌ Failed to save file: {e}")
        
        input("\nPress Enter to continue...")
    
    def _get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            # Connect to a remote address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"
    
    def _logout(self):
        """Logout current user"""
        print("\n--- Logout ---")
        confirm = input("Are you sure you want to logout? (y/n): ").lower()
        
        if confirm == 'y':
            # Cleanup connections
            self._cleanup()
            
            # Logout user
            self.user_manager.logout()
            
            print("✅ Logged out successfully.")
            
            # Start login flow again
            if not self._login_flow():
                self.running = False
    
    def _exit(self):
        """Exit the application"""
        print("\n--- Exit WhisperLink ---")
        confirm = input("Are you sure you want to exit? (y/n): ").lower()
        
        if confirm == 'y':
            self.running = False
    
    def _cleanup(self):
        """Cleanup resources before exit"""
        print("Cleaning up connections...")
        
        # Stop listening
        self.connection_manager.stop_listening()
        
        # Disconnect from all peers
        active_connections = self.connection_manager.get_active_connections()
        for conn in active_connections:
            self.connection_manager.disconnect_from_peer(conn.peer_id)
        
        print("✅ Cleanup completed.")

def main():
    """Main entry point for WhisperLink"""
    parser = argparse.ArgumentParser(
        description='WhisperLink - Secure P2P Encrypted Messenger',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  python whisperlink.py                    # Start WhisperLink CLI
  python whisperlink.py --version          # Show version
  python whisperlink.py --help             # Show this help
  
For more information, visit: https://github.com/CuzImSlymi/whisperlink
        '''
    )
    
    parser.add_argument(
        '--version', 
        action='version', 
        version='WhisperLink MVP v0.1.0'
    )
    
    parser.add_argument(
        '--data-dir',
        default='.whisperlink',
        help='Directory to store user data (default: .whisperlink)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    # Only parse args if running as main script
    if __name__ == "__main__":
        args = parser.parse_args()
    else:
        # Default args for import
        class Args:
            debug = False
            data_dir = '.whisperlink'
        args = Args()
    
    if args.debug:
        print("Debug mode enabled")
        print(f"Data directory: {args.data_dir}")
    
    try:
        # Create and start the CLI application
        app = WhisperLinkCLI()
        app.start()
    except KeyboardInterrupt:
        print("\n\nWhisperLink shutting down...")
    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
