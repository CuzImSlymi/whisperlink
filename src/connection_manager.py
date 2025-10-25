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
from models import Connection, Contact, User
from user_manager import UserManager
from contact_manager import ContactManager
from crypto_manager import CryptoManager
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver

class TunnelManager:
    """Manages tunnel connections for privacy using ngrok only"""
    
    def __init__(self):
        self.active_tunnels: Dict[int, str] = {}
        self.ws_bridge_port = 9002
        self.ws_bridge_running = False
        self.ngrok_process = None
    
    def create_tunnel(self, local_port: int) -> Optional[str]:
        try:
            if not self.ws_bridge_running:
                print(f"Starting WebSocket bridge for port {local_port}")
                if not self._start_websocket_bridge(local_port):
                    print("[ERROR] Failed to start WebSocket bridge")
                    return None
            
            return self._create_ngrok_tunnel(local_port)
        except Exception as e:
            print(f"[ERROR] Tunnel creation failed: {e}")
            return None
    
    def _create_ngrok_tunnel(self, local_port: int) -> Optional[str]:
        """
        Starts an ngrok tunnel, intelligently waiting for the API and capturing logs for debugging.
        """
        ngrok_logs = []
        log_thread = None
        
        try:
            print("Starting ngrok tunnel...")
            self._kill_existing_ngrok()
            
            # Start ngrok process and capture all its output
            self.ngrok_process = subprocess.Popen(
                ['ngrok', 'http', str(self.ws_bridge_port), '--log=stdout'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Thread to capture logs in real-time without blocking
            def capture_logs(process, log_list):
                try:
                    for line in iter(process.stdout.readline, ''):
                        log_list.append(line.strip())
                except Exception:
                    pass # stdout may be closed
            
            log_thread = threading.Thread(target=capture_logs, args=(self.ngrok_process, ngrok_logs))
            log_thread.daemon = True
            log_thread.start()
            
            print("Waiting for ngrok to establish tunnel...")
            tunnel_url = None
            api_ready = False
            
            # Poll the ngrok API for up to 16 seconds to get the tunnel URL
            for attempt in range(8):
                # Check if the process died prematurely
                if self.ngrok_process.poll() is not None:
                    print("[ERROR] ngrok process terminated unexpectedly.")
                    break
                
                try:
                    response = requests.get('http://localhost:4040/api/tunnels', timeout=2)
                    if response.status_code == 200:
                        api_ready = True
                        data = response.json()
                        tunnels = data.get('tunnels', [])
                        for tunnel in tunnels:
                            if tunnel.get('proto') == 'https':
                                tunnel_url = tunnel.get('public_url')
                                break
                        if tunnel_url:
                            break # Success! Found the URL.
                except requests.exceptions.ConnectionError:
                    if attempt == 0:
                        print("Waiting for ngrok API to become available...")
                    time.sleep(2)
                except Exception as e:
                    print(f"Error polling ngrok API: {e}")
                    time.sleep(2)
            
            if tunnel_url:
                print(f"[SUCCESS] ngrok tunnel created: {tunnel_url}")
                if self._test_tunnel_connectivity(tunnel_url):
                    self.active_tunnels[local_port] = tunnel_url
                    return tunnel_url
                else:
                    print("[ERROR] Tunnel created but is not responding to requests.")
                    self._kill_existing_ngrok()
                    return None
            else:
                # This is the failure case. We now print the logs.
                print("[ERROR] Failed to get tunnel URL from ngrok.")
                if not api_ready:
                    print("  The ngrok API server at http://localhost:4040 did not become available.")
                else:
                    print("  The API was available, but no HTTPS tunnel was found in the response.")
                
                self._kill_existing_ngrok()
                time.sleep(0.5) # Allow log thread to capture final output
                
                if ngrok_logs:
                    print("\n--- Last logs from ngrok process ---")
                    for log_line in ngrok_logs[-20:]: # Print last 20 lines
                        print(log_line)
                    print("------------------------------------")
                    print("\nHINT: Look for errors in the logs above. A common issue is a missing or invalid authtoken.")
                    print("  You can set one by running this command in your terminal:")
                    print("  ngrok config add-authtoken <YOUR_TOKEN>")
                
                return None
                
        except FileNotFoundError:
            print("[ERROR] ngrok not found. Please make sure it's installed and in your system's PATH.")
            print("  Download from https://ngrok.com/download")
            return None
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred with ngrok: {e}")
            self._kill_existing_ngrok()
            return None
    
    def _kill_existing_ngrok(self):
        try:
            if self.ngrok_process and self.ngrok_process.poll() is None:
                self.ngrok_process.terminate()
                self.ngrok_process.wait(timeout=5)
        except Exception:
            pass
        self.ngrok_process = None
        
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['taskkill', '/f', '/im', 'ngrok.exe'], check=False, capture_output=True)
            else:  # Unix/Linux/Mac
                subprocess.run(['pkill', '-f', 'ngrok'], check=False, capture_output=True)
        except Exception:
            pass
    
    def _test_tunnel_connectivity(self, tunnel_url: str) -> bool:
        try:
            print("Testing tunnel connectivity...")
            response = requests.get(tunnel_url + '/health', timeout=20)
            print(f"Tunnel test: HTTP {response.status_code}")
            return response.status_code < 599  # Any HTTP response is a sign of life
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
                await ws.prepare(request)
                
                try:
                    reader, writer = await asyncio.open_connection('127.0.0.1', tcp_port)
                    
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
                        
                except Exception as e:
                    print(f"WebSocket bridge error: {e}")
                finally:
                    if not ws.closed: 
                        await ws.close()
                
                return ws
            
            # Add a simple health check endpoint for ngrok
            async def health_check(request):
                return web.Response(text="WhisperLink Bridge OK")
            
            # Add a root handler that returns basic info for regular HTTP requests
            async def root_handler(request):
                # Check if this is a WebSocket upgrade request
                if request.headers.get('Upgrade', '').lower() == 'websocket':
                    return await websocket_handler(request)
                else:
                    # Return a simple HTML page for regular HTTP requests
                    html = """
                    <html>
                    <head><title>WhisperLink Bridge</title></head>
                    <body>
                        <h1>WhisperLink WebSocket Bridge</h1>
                        <p>This is a WebSocket bridge endpoint.</p>
                        <p>Connect using a WebSocket client to establish a connection.</p>
                    </body>
                    </html>
                    """
                    return web.Response(text=html, content_type='text/html')
            
            async def start_server():
                app = web.Application()
                # Use root_handler for both WebSocket and regular HTTP requests at root
                app.router.add_get('/', root_handler)
                app.router.add_get('/ws', websocket_handler)  # Alternative WebSocket endpoint
                app.router.add_get('/health', health_check)  # Health check endpoint
                
                runner = web.AppRunner(app)
                await runner.setup()
                site = web.TCPSite(runner, '0.0.0.0', self.ws_bridge_port)
                
                try:
                    await site.start()
                    print(f"[SUCCESS] aiohttp WebSocket bridge running on port {self.ws_bridge_port}")
                    await asyncio.Event().wait()  # Run forever
                finally:
                    await runner.cleanup()
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start_server())
        
        bridge_thread = threading.Thread(target=run_aiohttp_bridge, daemon=True)
        bridge_thread.start()
        
        print("Waiting for WebSocket bridge to start...")
        time.sleep(4)
        
        for i in range(8):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    if s.connect_ex(('127.0.0.1', self.ws_bridge_port)) == 0:
                        print(f"[SUCCESS] WebSocket bridge verified running on port {self.ws_bridge_port}")
                        self.ws_bridge_running = True
                        return True
            except Exception: 
                pass
            time.sleep(2)
        
        print("[ERROR] WebSocket bridge failed to start")
        return False
    
    def close_tunnel(self, local_port: int):
        if local_port in self.active_tunnels:
            del self.active_tunnels[local_port]
        self._kill_existing_ngrok()
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
                    return False, "[ERROR] Failed to create tunnel. Try direct IP connection instead."
            
            return True, connection_info
        except Exception as e:
            return False, f"[ERROR] Failed to start listening: {str(e)}"
    
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

            # If the connecting user is not a contact, add them. This is crucial for message exchange.
            if not self.contact_manager.get_contact(peer_id):
                print(f"Received connection from new peer '{peer_username}'. Adding to contacts.")
                self.contact_manager.add_contact(
                    contact_user_id=peer_id,
                    username=peer_username,
                    public_key=peer_public_key,
                    connection_type="direct", # Assume direct, as we don't have tunnel info
                    address=f"{client_address[0]}:{client_address[1]}"
                )
            
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
            
            print(f"\n[SUCCESS] Incoming connection established with {peer_username}")
            
            # Start a dedicated thread for handling messages, mirroring the outgoing connection logic
            message_thread = threading.Thread(
                target=self._handle_peer_messages,
                args=(peer_id,),
                daemon=True
            )
            message_thread.start()
        
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
            print(f"[ERROR] Failed to connect to peer: {e}")
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
            
            print(f"[SUCCESS] Successfully connected to {contact.username}")
            return True
        
        except Exception as e:
            print(f"[ERROR] Direct connection failed: {e}")
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
            
            # Create a placeholder connection to show "connecting" status in UI
            self.connections[peer_id] = Connection(
                peer_id=peer_id,
                peer_username=contact.username,
                connection_type="tunnel_websocket",
                address="tunnel",
                port=0,
                status="connecting",
                established_at=datetime.now().isoformat(),
            )
            
            def run_async_connect():
                # Each connection gets its own event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self._async_tunnel_connect(peer_id, contact, handshake, loop))
                    # If the connection was successful, the loop will have tasks (message handler)
                    # and we run it forever to keep it alive.
                    if not loop.is_closed() and self.connections.get(peer_id):
                        loop.run_forever()
                except Exception as e:
                    print(f"[ERROR] Tunnel connection thread error: {e}")
                    self.disconnect_from_peer(peer_id)
                finally:
                    # Final cleanup of the loop
                    if not loop.is_closed():
                        if loop.is_running():
                            loop.stop()
                        loop.close()
            
            connect_thread = threading.Thread(target=run_async_connect, daemon=True)
            connect_thread.start()
            
            # Immediately return True to indicate the connection process has started
            return True
            
        except Exception as e:
            print(f"[ERROR] Tunnel connection failed: {e}")
            self.disconnect_from_peer(peer_id) # Clean up placeholder
            return False

    async def _async_tunnel_connect(self, peer_id: str, contact: Contact, handshake: dict, loop: asyncio.AbstractEventLoop):
        try:
            tunnel_url = contact.tunnel_url.rstrip('/')
            print(f"Connecting to: {tunnel_url}")
            await self._try_websocket_connection(peer_id, contact, handshake, tunnel_url, loop)
        except Exception as e:
            print(f"[ERROR] Tunnel connection error: {e}")
            self.disconnect_from_peer(peer_id) # Clean up on failure
            raise # Re-raise to be caught by the thread's error handler

    async def _try_websocket_connection(self, peer_id: str, contact: Contact, handshake: dict, tunnel_url: str, loop: asyncio.AbstractEventLoop):
        import websockets  # Use websockets for the client side
        
        ws_base_url = tunnel_url.replace('https://', 'wss://').replace('http://', 'ws://')
        headers = {'User-Agent': 'WhisperLink/1.0', 'ngrok-skip-browser-warning': 'true'}
        
        ssl_context = None
        if ws_base_url.startswith('wss://'):
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        for ws_path in ['/ws', '']:
            ws_url = ws_base_url + ws_path
            print(f"Attempting WebSocket connection to: {ws_url}")
            
            try:
                websocket = await asyncio.wait_for(websockets.connect(
                    ws_url, additional_headers=headers, ssl=ssl_context, 
                    open_timeout=20, ping_interval=30, ping_timeout=10
                ), timeout=25.0)
                
                await websocket.send(json.dumps(handshake))
                response_data = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                response = json.loads(response_data)
                
                if response.get('status') == 'accepted':
                    connection = self.connections.get(peer_id)
                    if connection:
                        connection.status = "connected"
                        connection.established_at = datetime.now().isoformat()
                        connection.websocket_obj = websocket
                        connection.asyncio_loop = loop # Store the loop with the connection
                        self.contact_manager.update_contact_last_seen(peer_id)
                        print(f"[SUCCESS] Successfully connected to {contact.username} via tunnel")
                        # Start the message handler as a task on this connection's loop
                        loop.create_task(self._handle_websocket_messages_native(peer_id, websocket))
                        return # Exit the function on success
                else:
                    await websocket.close()
                    print("[ERROR] Handshake rejected by peer")
                    self.disconnect_from_peer(peer_id)
                    return # Handshake failed, stop trying
                    
            except asyncio.TimeoutError:
                print(f"[ERROR] Connection timeout for {ws_url}")
                continue
            except Exception as e:
                if 'HTTP 404' in str(e):
                    print(f"[ERROR] Path not found at {ws_url}, trying fallback...")
                else:
                    print(f"[ERROR] WebSocket connection failed for {ws_url}: {e}")
                continue
        
        print("[ERROR] All WebSocket connection attempts failed")
        self.disconnect_from_peer(peer_id)
    
    def _handle_peer_messages(self, peer_id: str):
        connection = self.connections.get(peer_id)
        if not connection or not connection.socket_obj: return
        
        try:
            while connection.status == "connected":
                data = connection.socket_obj.recv(4096)
                if not data: break
                
                try:
                    message_data = json.loads(data.decode())
                    if message_data.get('type') == 'chat':
                        current_user = self.user_manager.get_current_user()
                        contact = self.contact_manager.get_contact(peer_id)
                        
                        if current_user and contact:
                            crypto = CryptoManager()
                            decrypted = crypto.decrypt_message(current_user.private_key, contact.public_key, message_data.get('message'))
                            for handler in self.message_handlers:
                                handler(peer_id, connection.peer_username, decrypted, message_data.get('timestamp'))
                except json.JSONDecodeError: continue
        except Exception: pass
        finally:
            self.disconnect_from_peer(peer_id)
    
    async def _handle_websocket_messages_native(self, peer_id: str, websocket):
        try:
            async for message in websocket:
                try:
                    message_data = json.loads(message)
                    if message_data.get('type') == 'chat':
                        current_user = self.user_manager.get_current_user()
                        contact = self.contact_manager.get_contact(peer_id)
                        
                        if current_user and contact:
                            crypto = CryptoManager()
                            decrypted = crypto.decrypt_message(current_user.private_key, contact.public_key, message_data.get('message'))
                            for handler in self.message_handlers:
                                handler(peer_id, contact.username, decrypted, message_data.get('timestamp'))
                except json.JSONDecodeError: continue
        except Exception: pass
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
            encrypted_message = crypto.encrypt_message(current_user.private_key, contact.public_key, message)
            message_data = {'type': 'chat', 'message': encrypted_message, 'timestamp': datetime.now().isoformat()}
            
            # For outgoing WebSocket connections, use the loop stored on the connection object
            if connection.websocket_obj and connection.asyncio_loop and connection.asyncio_loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._send_websocket_message(connection.websocket_obj, message_data),
                    connection.asyncio_loop
                )
                return True
            # For incoming connections (which use the bridge), use the socket object
            elif connection.socket_obj:
                connection.socket_obj.sendall(json.dumps(message_data).encode())
                return True
            
            return False
        except Exception as e:
            print(f"[ERROR] Failed to send message: {e}")
            return False
    
    async def _send_websocket_message(self, websocket, message_data):
        try:
            await websocket.send(json.dumps(message_data))
        except Exception as e:
            print(f"[ERROR] Failed to send WebSocket message: {e}")
    
    def disconnect_from_peer(self, peer_id: str):
        if peer_id in self.connections:
            connection = self.connections.pop(peer_id)
            connection.status = "disconnected"
            
            if connection.socket_obj:
                try: connection.socket_obj.close()
                except: pass
            
            # When disconnecting a WebSocket, also stop its dedicated event loop
            if connection.websocket_obj and connection.asyncio_loop and connection.asyncio_loop.is_running():
                try:
                    # Close the socket from within its own loop
                    asyncio.run_coroutine_threadsafe(connection.websocket_obj.close(), connection.asyncio_loop)
                    # Stop the loop
                    connection.asyncio_loop.call_soon_threadsafe(connection.asyncio_loop.stop)
                except: pass
            
            print(f"\nDisconnected from {connection.peer_username}")
    
    def get_active_connections(self) -> List[Connection]:
        return list(self.connections.values())
    
    def get_connection(self, peer_id: str) -> Optional[Connection]:
        return self.connections.get(peer_id)