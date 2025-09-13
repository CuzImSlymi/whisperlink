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
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver

class TunnelManager:
    """Manages tunnel connections for privacy using ngrok only"""

    def __init__(self):
        self.active_tunnels: Dict[int, str] = {}
        self.ws_bridge_port = 9002
        self.ws_bridge_running = False
        self.ws_bridge_server = None
        self.ngrok_process = None
        self.http_server = None

    def create_tunnel(self, local_port: int) -> Optional[str]:
        try:
            if not self.ws_bridge_running:
                print(f"Starting WebSocket bridge for port {local_port}")
                if not self._start_websocket_bridge(local_port):
                    print("❌ Failed to start WebSocket bridge")
                    return None
            return self._create_ngrok_tunnel(local_port)
        except Exception as e:
            print(f"❌ Tunnel creation failed: {e}")
            return None

    def _create_ngrok_tunnel(self, local_port: int) -> Optional[str]:
        try:
            print("Starting ngrok tunnel...")
            self._kill_existing_ngrok()
            self.ngrok_process = subprocess.Popen([
                'ngrok', 'http', str(self.ws_bridge_port), '--log=stdout'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            print("Waiting for ngrok to establish tunnel...")
            time.sleep(10)  # Longer initial wait

            # Retry logic for ngrok API
            tunnel_url = None
            for attempt in range(8):  # More attempts
                try:
                    response = requests.get('http://localhost:4040/api/tunnels', timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        tunnels = data.get('tunnels', [])
                        for tunnel in tunnels:
                            if tunnel.get('proto') == 'https':
                                tunnel_url = tunnel.get('public_url')
                                break
                        if tunnel_url:
                            break
                except requests.exceptions.ConnectionError:
                    print(f"Waiting for ngrok API... (attempt {attempt + 1}/8)")
                    time.sleep(3)

            if tunnel_url:
                print(f"✅ ngrok tunnel created: {tunnel_url}")
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
            print(" Download from https://ngrok.com/download")
            print(" Or install: brew install ngrok (macOS) / choco install ngrok (Windows)")
            return None
        except Exception as e:
            print(f"❌ ngrok error: {e}")
            self._kill_existing_ngrok()
            return None

    def _kill_existing_ngrok(self):
        try:
            if self.ngrok_process:
                self.ngrok_process.terminate()
                self.ngrok_process.wait(timeout=5)
                self.ngrok_process = None
        except:
            pass

        try:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/f', '/im', 'ngrok.exe'], capture_output=True)
            else:
                subprocess.run(['pkill', '-f', 'ngrok'], capture_output=True)
        except:
            pass

    def _test_tunnel_connectivity(self, tunnel_url: str) -> bool:
        try:
            print("Testing tunnel connectivity...")
            response = requests.get(tunnel_url, timeout=20)
            print(f"Tunnel test: HTTP {response.status_code}")
            return response.status_code in [200, 404]  # 404 is OK for WebSocket endpoint
        except Exception as e:
            print(f"Tunnel test failed: {e}")
            return False

    def _start_websocket_bridge(self, tcp_port: int) -> bool:
        """Start HTTP server that handles both HTTP requests and WebSocket upgrades"""
        
        class BridgeHandler(BaseHTTPRequestHandler):
            def __init__(self, tcp_port, *args, **kwargs):
                self.tcp_port = tcp_port
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                if self.headers.get('Upgrade', '').lower() == 'websocket':
                    # This is a WebSocket upgrade request, let websockets handle it
                    return
                else:
                    # Regular HTTP request - respond with 200 OK
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'WebSocket bridge is running')
            
            def log_message(self, format, *args):
                return  # Suppress HTTP server logs

        def run_hybrid_server():
            class HybridServer:
                def __init__(self, tcp_port):
                    self.tcp_port = tcp_port
                    self.running = False
                
                async def handle_websocket(self, websocket, path):
                    try:
                        print(f"WebSocket client connected from {websocket.remote_address}")
                        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        tcp_sock.settimeout(10)
                        try:
                            tcp_sock.connect(('127.0.0.1', self.tcp_port))
                            print(f"Connected to TCP server at 127.0.0.1:{self.tcp_port}")
                        except Exception as e:
                            print(f"Failed to connect to TCP server: {e}")
                            tcp_sock.close()
                            return

                        async def tcp_to_ws():
                            try:
                                loop = asyncio.get_event_loop()
                                while True:
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

                        await asyncio.gather(tcp_to_ws(), ws_to_tcp(), return_exceptions=True)
                    except Exception as e:
                        print(f"Bridge connection error: {e}")

                async def start_servers(self):
                    print(f"Starting hybrid server on 0.0.0.0:{self.ws_bridge_port} -> 127.0.0.1:{self.tcp_port}")
                    
                    # Start WebSocket server
                    try:
                        self.ws_bridge_server = await websockets.serve(
                            self.handle_websocket,
                            '0.0.0.0',
                            self.ws_bridge_port,
                            ping_interval=30,
                            ping_timeout=15,
                            max_size=1048576,
                            compression=None,
                            process_request=self.process_request
                        )
                        self.ws_bridge_running = True
                        print(f"✅ Hybrid bridge running on port {self.ws_bridge_port}")
                        await self.ws_bridge_server.wait_closed()
                    except Exception as e:
                        print(f"❌ Failed to start hybrid bridge: {e}")
                        self.ws_bridge_running = False

                async def process_request(self, path, request_headers):
                    # Handle regular HTTP requests
                    if request_headers.get('upgrade', '').lower() != 'websocket':
                        return (200, [('Content-Type', 'text/plain')], b'WebSocket bridge is running\n')
                    # Let WebSocket upgrade proceed normally
                    return None

            hybrid_server = HybridServer(tcp_port)
            asyncio.run(hybrid_server.start_servers())

        bridge_thread = threading.Thread(target=run_hybrid_server, daemon=True)
        bridge_thread.start()
        
        print("Waiting for hybrid bridge to start...")
        time.sleep(5)  # Longer wait time

        # Verify bridge is running with HTTP test
        max_retries = 8
        for i in range(max_retries):
            try:
                response = requests.get(f'http://127.0.0.1:{self.ws_bridge_port}', timeout=5)
                if response.status_code == 200:
                    print(f"✅ Hybrid bridge verified running on port {self.ws_bridge_port}")
                    self.ws_bridge_running = True
                    return True
            except:
                pass
            
            if i < max_retries - 1:
                print(f"Waiting for hybrid bridge... ({i+1}/{max_retries})")
                time.sleep(3)
        
        print("❌ Hybrid bridge failed to start")
        return False

    def close_tunnel(self, local_port: int):
        if local_port in self.active_tunnels:
            del self.active_tunnels[local_port]
        self._kill_existing_ngrok()
        if self.ws_bridge_server:
            try:
                self.ws_bridge_server.close()
            except:
                pass
        if self.http_server:
            try:
                self.http_server.shutdown()
            except:
                pass
        self.ws_bridge_running = False

    def get_tunnel_url(self, local_port: int) -> Optional[str]:
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
        self.message_handlers.append(handler)

    def start_listening(self, port: int = 0, use_tunnel: bool = False) -> Tuple[bool, str]:
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', port))
            self.server_socket.listen(5)
            self.server_port = self.server_socket.getsockname()[1]
            self.listening = True

            listen_thread = threading.Thread(target=self._listen_for_connections, daemon=True)
            listen_thread.start()
            connection_info = f"localhost:{self.server_port}"

            if use_tunnel:
                print("Creating secure tunnel (this may take a moment)...")
                tunnel_url = self.tunnel_manager.create_tunnel(self.server_port)
                if tunnel_url:
                    connection_info = tunnel_url
                else:
                    self.stop_listening()
                    return False, "❌ Failed to create tunnel. Try direct IP connection instead."

            return True, connection_info
        except Exception as e:
            return False, f"❌ Failed to start listening: {str(e)}"

    def stop_listening(self):
        self.listening = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        self.server_socket = None
        if self.server_port:
            self.tunnel_manager.close_tunnel(self.server_port)

    def _listen_for_connections(self):
        while self.listening and self.server_socket:
            try:
                client_socket, client_address = self.server_socket.accept()
                handle_thread = threading.Thread(
                    target=self._handle_incoming_connection,
                    args=(client_socket, client_address),
                    daemon=True
                )
                handle_thread.start()
            except Exception as e:
                if self.listening:
                    print(f"Error accepting connection: {e}")
                break

    def _handle_incoming_connection(self, client_socket: socket.socket, client_address: tuple):
        try:
            handshake_data = client_socket.recv(1024).decode()
            handshake = json.loads(handshake_data)
            peer_id = handshake.get('user_id')
            peer_username = handshake.get('username')
            peer_public_key = handshake.get('public_key')

            if not all([peer_id, peer_username, peer_public_key]):
                client_socket.close()
                return

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
            self.contact_manager.update_contact_last_seen(peer_id)
            print(f"\n✅ Incoming connection established with {peer_username}")
            self._handle_peer_messages(peer_id)

        except Exception as e:
            print(f"Error handling incoming connection: {e}")
            try:
                client_socket.close()
            except:
                pass

    def connect_to_peer(self, peer_id: str) -> bool:
        contact = self.contact_manager.get_contact(peer_id)
        if not contact:
            return False

        current_user = self.user_manager.get_current_user()
        if not current_user:
            return False

        try:
            if contact.connection_type == "direct" and contact.address:
                return self._connect_direct(peer_id, contact, current_user)
            elif contact.connection_type == "tunnel" and contact.tunnel_url:
                return self._connect_via_tunnel(peer_id, contact, current_user)
            else:
                return False
        except Exception as e:
            print(f"❌ Failed to connect to peer: {e}")
            return False

    def _connect_direct(self, peer_id: str, contact: Contact, current_user: User) -> bool:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)
            host, port = contact.address.split(':')
            client_socket.connect((host, int(port)))

            handshake = {
                'user_id': current_user.user_id,
                'username': current_user.username,
                'public_key': current_user.public_key
            }
            client_socket.send(json.dumps(handshake).encode())
            response_data = client_socket.recv(1024).decode()
            response = json.loads(response_data)

            if response.get('status') != 'accepted':
                client_socket.close()
                return False

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

            message_thread = threading.Thread(
                target=self._handle_peer_messages,
                args=(peer_id,), daemon=True
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
        print(f"Connecting to {contact.username} via tunnel...")
        try:
            handshake = {
                'user_id': current_user.user_id,
                'username': current_user.username,
                'public_key': current_user.public_key
            }
            result = [False]

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
            connect_thread.join(timeout=30)
            return result[0]

        except Exception as e:
            print(f"❌ Tunnel connection failed: {e}")
            return False

    async def _async_tunnel_connect(self, peer_id: str, contact: Contact, handshake: dict) -> bool:
        try:
            tunnel_url = contact.tunnel_url.rstrip('/')
            print(f"Connecting to: {tunnel_url}")
            return await self._try_websocket_connection(peer_id, contact, handshake, tunnel_url)
        except Exception as e:
            print(f"❌ Tunnel connection error: {e}")
            return False

    async def _try_websocket_connection(self, peer_id: str, contact: Contact, handshake: dict, tunnel_url: str):
        import websockets
        ws_url = tunnel_url.replace('https://', 'wss://').replace('http://', 'ws://')
        headers = {
            'User-Agent': 'WhisperLink/1.0',
            'Origin': tunnel_url
        }

        ssl_context = None
        if ws_url.startswith('wss://'):
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        print(f"Attempting WebSocket connection to: {ws_url}")
        try:
            websocket = await asyncio.wait_for(websockets.connect(
                ws_url,
                extra_headers=headers,
                ssl=ssl_context,
                open_timeout=20,
                ping_interval=30,
                ping_timeout=15,
                max_size=1048576,
                compression=None
            ), timeout=25.0)

            await websocket.send(json.dumps(handshake))
            response_data = await asyncio.wait_for(websocket.recv(), timeout=15.0)
            response = json.loads(response_data)

            if response.get('status') == 'accepted':
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
                self.contact_manager.update_contact_last_seen(peer_id)
                print(f"✅ Successfully connected to {contact.username} via tunnel")
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
        connection = self.connections.get(peer_id)
        if not connection or not connection.socket_obj:
            return

        try:
            while connection.status == "connected":
                data = connection.socket_obj.recv(4096)
                if not data:
                    break
                try:
                    message_data = json.loads(data.decode())
                    message_type = message_data.get('type')
                    if message_type == 'chat':
                        encrypted_message = message_data.get('message')
                        timestamp = message_data.get('timestamp')
                        current_user = self.user_manager.get_current_user()
                        contact = self.contact_manager.get_contact(peer_id)
                        if current_user and contact:
                            crypto = CryptoManager()
                            decrypted_message = crypto.decrypt_message(
                                current_user.private_key,
                                contact.public_key,
                                encrypted_message
                            )
                            for handler in self.message_handlers:
                                handler(peer_id, connection.peer_username, decrypted_message, timestamp)
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            print(f"Error handling messages from {peer_id}: {e}")
        finally:
            connection.status = "disconnected"
            try:
                connection.socket_obj.close()
            except:
                pass

    async def _handle_websocket_messages_native(self, peer_id: str, websocket):
        try:
            async for message in websocket:
                try:
                    message_data = json.loads(message)
                    message_type = message_data.get('type')
                    if message_type == 'chat':
                        encrypted_message = message_data.get('message')
                        timestamp = message_data.get('timestamp')
                        current_user = self.user_manager.get_current_user()
                        contact = self.contact_manager.get_contact(peer_id)
                        if current_user and contact:
                            crypto = CryptoManager()
                            decrypted_message = crypto.decrypt_message(
                                current_user.private_key,
                                contact.public_key,
                                encrypted_message
                            )
                            for handler in self.message_handlers:
                                handler(peer_id, contact.username, decrypted_message, timestamp)
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            print(f"Error handling WebSocket messages from {peer_id}: {e}")
        finally:
            if peer_id in self.connections:
                self.connections[peer_id].status = "disconnected"
                del self.connections[peer_id]

    def send_message(self, peer_id: str, message: str) -> bool:
        connection = self.connections.get(peer_id)
        if not connection or connection.status != "connected":
            return False

        current_user = self.user_manager.get_current_user()
        contact = self.contact_manager.get_contact(peer_id)
        if not current_user or not contact:
            return False

        try:
            crypto = CryptoManager()
            encrypted_message = crypto.encrypt_message(
                current_user.private_key,
                contact.public_key,
                message
            )
            message_data = {
                'type': 'chat',
                'message': encrypted_message,
                'timestamp': datetime.now().isoformat()
            }

            if connection.websocket_obj:
                asyncio.create_task(self._send_websocket_message(connection.websocket_obj, message_data))
                return True
            elif connection.socket_obj:
                connection.socket_obj.send(json.dumps(message_data).encode())
                return True
            else:
                return False
        except Exception as e:
            print(f"❌ Failed to send message: {e}")
            return False

    async def _send_websocket_message(self, websocket, message_data):
        try:
            await websocket.send(json.dumps(message_data))
        except Exception as e:
            print(f"❌ Failed to send WebSocket message: {e}")

    def disconnect_from_peer(self, peer_id: str):
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
        return [conn for conn in self.connections.values() if conn.status == "connected"]

    def get_connection(self, peer_id: str) -> Optional[Connection]:
        return self.connections.get(peer_id)
