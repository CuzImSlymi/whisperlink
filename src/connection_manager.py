import os
import uuid
import json
import socket
import threading
import subprocess
import asyncio
import ssl
import urllib.parse
import requests
import time
import http
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .models import Connection, Contact, User
from .user_manager import UserManager
from .contact_manager import ContactManager
from .crypto_manager import CryptoManager
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver

# aiohttp is now used for the bridge, but we import it inside the thread
# to avoid potential multi-threading issues with asyncio loops.
# We also remove the direct import of websockets as it's no longer used for the server.

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
                'ngrok', 'http', str(self.ws_bridge_port), '--log=stdout', '--host-header=rewrite'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            print("Waiting for ngrok to establish tunnel...")
            time.sleep(8) # Reduced sleep, aiohttp is faster to start

            tunnel_url = None
            for attempt in range(8):
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
                subprocess.run(['taskkill', '/f', '/im', 'ngrok.exe'], capture_output=True, check=False)
            else:
                subprocess.run(['pkill', '-f', 'ngrok'], capture_output=True, check=False)
        except:
            pass

    def _test_tunnel_connectivity(self, tunnel_url: str) -> bool:
        try:
            print("Testing tunnel connectivity...")
            response = requests.get(tunnel_url, timeout=20)
            print(f"Tunnel test: HTTP {response.status_code}")
            # ngrok often returns 502 temporarily, but any HTTP response is a success
            return response.status_code < 599
        except Exception as e:
            print(f"Tunnel test failed: {e}")
            return False

    def _start_websocket_bridge(self, tcp_port: int) -> bool:
        """Start a robust WebSocket server using aiohttp that bridges to TCP."""

        def run_aiohttp_bridge():
            import asyncio
            from aiohttp import web, WSMsgType

            async def websocket_handler(request):
                ws = web.WebSocketResponse()

                if not ws.can_prepare(request):
                    print("Bridge: Received plain HTTP request (likely ngrok health check). Responding OK.")
                    return web.Response(text="OK")

                await ws.prepare(request)
                print(f"Bridge: WebSocket client connected from {request.remote}")

                try:
                    reader, writer = await asyncio.open_connection('127.0.0.1', tcp_port)
                    print(f"Bridge: TCP connection established to 127.0.0.1:{tcp_port}")

                    async def ws_to_tcp():
                        try:
                            async for msg in ws:
                                if msg.type in (WSMsgType.TEXT, WSMsgType.BINARY):
                                    data = msg.data if msg.type == WSMsgType.BINARY else msg.data.encode('utf-8')
                                    writer.write(data)
                                    await writer.drain()
                                elif msg.type == WSMsgType.ERROR:
                                    break
                        finally:
                            if not writer.is_closing():
                                writer.close()
                                await writer.wait_closed()

                    async def tcp_to_ws():
                        try:
                            while not reader.at_eof():
                                data = await reader.read(4096)
                                if not data:
                                    break
                                await ws.send_bytes(data)
                        finally:
                            if not ws.closed:
                                await ws.close()

                    done, pending = await asyncio.wait(
                        [asyncio.create_task(ws_to_tcp()), asyncio.create_task(tcp_to_ws())],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    for task in pending:
                        task.cancel()

                except ConnectionRefusedError:
                    print(f"❌ Bridge: TCP connection refused for port {tcp_port}.")
                except Exception as e:
                    print(f"❌ Bridge: An error occurred in handler: {e}")
                finally:
                    print("Bridge: Connection closing.")
                    if not ws.closed:
                       await ws.close()
                return ws

            async def start_server():
                app = web.Application()
                app.router.add_route('GET', '/', websocket_handler)
                runner = web.AppRunner(app)
                await runner.setup()
                site = web.TCPSite(runner, '0.0.0.0', self.ws_bridge_port)
                try:
                    await site.start()
                    print(f"✅ aiohttp WebSocket bridge running on port {self.ws_bridge_port}")
                    while True:
                        await asyncio.sleep(3600)
                except Exception as e:
                    print(f"❌ Failed to start aiohttp bridge: {e}")
                finally:
                    await runner.cleanup()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start_server())

        bridge_thread = threading.Thread(target=run_aiohttp_bridge, daemon=True)
        bridge_thread.start()

        print("Waiting for WebSocket bridge to start...")
        time.sleep(5)

        max_retries = 8
        for i in range(max_retries):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_sock:
                    test_sock.settimeout(2)
                    result = test_sock.connect_ex(('127.0.0.1', self.ws_bridge_port))
                    if result == 0:
                        print(f"✅ WebSocket bridge verified running on port {self.ws_bridge_port}")
                        self.ws_bridge_running = True
                        return True
            except Exception:
                pass
            
            if i < max_retries - 1:
                print(f"Waiting for WebSocket bridge... ({i+1}/{max_retries})")
                time.sleep(3)

        print("❌ WebSocket bridge failed to start")
        return False


    def close_tunnel(self, local_port: int):
        if local_port in self.active_tunnels:
            del self.active_tunnels[local_port]
        self._kill_existing_ngrok()
        # No server objects to close directly as they are managed in the thread
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
        import websockets # Use websockets for the client side

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
            # Silencing some common errors on disconnect
            if "socket" not in str(e) and "Connection" not in str(e):
                 print(f"Error handling messages from {peer_id}: {e}")
        finally:
            self.disconnect_from_peer(peer_id)


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
            if "Connection" not in str(e): # Silence common disconnect errors
                print(f"Error handling WebSocket messages from {peer_id}: {e}")
        finally:
            self.disconnect_from_peer(peer_id)

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
                # Need to run this in the correct event loop
                asyncio.run_coroutine_threadsafe(
                    self._send_websocket_message(connection.websocket_obj, message_data),
                    asyncio.get_running_loop()
                )
                return True
            elif connection.socket_obj:
                connection.socket_obj.sendall(json.dumps(message_data).encode())
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
        if peer_id in self.connections:
            connection = self.connections.pop(peer_id)
            connection.status = "disconnected"
            if connection.socket_obj:
                try:
                    connection.socket_obj.close()
                except:
                    pass
            if connection.websocket_obj:
                try:
                    # Close websocket connection from the appropriate loop
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.run_coroutine_threadsafe(connection.websocket_obj.close(), loop)
                    else:
                        loop.run_until_complete(connection.websocket_obj.close())
                except:
                    pass
            print(f"\nDisconnected from {connection.peer_username}")


    def get_active_connections(self) -> List[Connection]:
        return [conn for conn in self.connections.values() if conn.status == "connected"]

    def get_connection(self, peer_id: str) -> Optional[Connection]:
        return self.connections.get(peer_id)