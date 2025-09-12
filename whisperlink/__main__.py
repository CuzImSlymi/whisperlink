import asyncio
import base64
import json
import os
import socket
import ipaddress
import urllib.parse
from pathlib import Path

import click
import websockets
from nacl import pwhash, secret, signing, utils
from nacl.public import Box, PrivateKey, PublicKey


DEFAULT_BASE = Path('.whisperlink')


def ensure_store(base: Path) -> None:
    base.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data)
    os.chmod(path, 0o600)


def read_text(path: Path) -> str:
    return path.read_text()


def seal_secret(password: str, plaintext: bytes) -> bytes:
    salt = utils.random(pwhash.argon2id.SALTBYTES)
    kdf_key = pwhash.argon2id.kdf(
        secret.SecretBox.KEY_SIZE,
        password.encode('utf-8'),
        salt,
        opslimit=pwhash.argon2id.OPSLIMIT_MODERATE,
        memlimit=pwhash.argon2id.MEMLIMIT_MODERATE,
    )
    box = secret.SecretBox(kdf_key)
    nonce = utils.random(secret.SecretBox.NONCE_SIZE)
    ct = box.encrypt(plaintext, nonce)
    return salt + ct


def open_secret(password: str, sealed: bytes) -> bytes:
    salt = sealed[: pwhash.argon2id.SALTBYTES]
    ct = sealed[pwhash.argon2id.SALTBYTES :]
    kdf_key = pwhash.argon2id.kdf(
        secret.SecretBox.KEY_SIZE,
        password.encode('utf-8'),
        salt,
        opslimit=pwhash.argon2id.OPSLIMIT_MODERATE,
        memlimit=pwhash.argon2id.MEMLIMIT_MODERATE,
    )
    box = secret.SecretBox(kdf_key)
    return box.decrypt(ct)


def b64e(b: bytes) -> str:
    return base64.b64encode(b).decode('ascii')


def b64d(s: str) -> bytes:
    return base64.b64decode(s.encode('ascii'))


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('--name', required=True, help='Local profile name (directory under .whisperlink)')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
@click.option('--base', type=click.Path(path_type=Path), default=DEFAULT_BASE)
def register(name: str, password: str, base: Path) -> None:
    """Generate identity keys and store them locally, encrypted with password."""
    store = Path(base) / name
    ensure_store(store)

    # Signing/identity keypair
    signing_key = signing.SigningKey.generate()
    verify_key = signing_key.verify_key

    # Curve25519 for encryption
    priv = PrivateKey.generate()
    pub = priv.public_key

    identity = {
        'name': name,
        'verify_key': b64e(bytes(verify_key)),
        'public_key': b64e(bytes(pub)),
    }

    sealed_sign = seal_secret(password, bytes(signing_key))
    sealed_priv = seal_secret(password, bytes(priv))

    write_text(store / 'identity.json', json.dumps(identity, indent=2))
    (store / 'private').mkdir(parents=True, exist_ok=True)
    (store / 'public.key').write_text(b64e(bytes(pub)))
    os.chmod(store / 'public.key', 0o644)
    (store / 'private' / 'signing.key').write_bytes(sealed_sign)
    (store / 'private' / 'encrypt.key').write_bytes(sealed_priv)

    click.echo(f"Registered {name}. Public Key: {identity['public_key']}")


def load_keys(store: Path, password: str) -> tuple[PrivateKey, signing.SigningKey, PublicKey]:
    enc = open_secret(password, (store / 'private' / 'encrypt.key').read_bytes())
    sign = open_secret(password, (store / 'private' / 'signing.key').read_bytes())
    priv = PrivateKey(enc)
    signing_key = signing.SigningKey(sign)
    pub = priv.public_key
    return priv, signing_key, pub


async def handle_client(conn: socket.socket, box: Box) -> None:
    with conn:
        data = conn.recv(4096)
        if not data:
            return
        plaintext = box.decrypt(data)
        print(f"Received: {plaintext.decode('utf-8', 'ignore')}")
        reply = box.encrypt(b"ack")
        conn.sendall(reply)


@cli.command('start-server')
@click.option('--store', type=click.Path(path_type=Path), required=True)
@click.option('--password', prompt=True, hide_input=True)
@click.option('--port', type=int, default=9001)
@click.option('--bind', default='127.0.0.1', help='Interface/IP to bind the server (use 0.0.0.0 for all)')
@click.option('--peer-key', required=True, help='Peer base64 public key')
@click.option('--lan-only/--no-lan-only', default=False, help='Only accept clients from the same LAN subnet')
@click.option('--cidr', default=None, help='CIDR for allowed subnet (e.g., 192.168.1.0/24). Default infers /24 from --bind')
def start_server(store: Path, password: str, port: int, bind: str, peer_key: str, lan_only: bool, cidr: str | None) -> None:
    """Start a simple TCP listener and decrypt messages from a known peer."""
    priv, _sign, _pub = load_keys(store, password)
    peer = PublicKey(b64d(peer_key))
    box = Box(priv, peer)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((bind, port))
    sock.listen(5)
    print(f"Listening on {bind}:{port}")

    allowed_network: ipaddress.IPv4Network | None = None
    try:
        if lan_only:
            if cidr:
                allowed_network = ipaddress.ip_network(cidr, strict=False)  # type: ignore[assignment]
            else:
                bind_net = ipaddress.ip_network(f"{bind}/24", strict=False)
                allowed_network = bind_net  # type: ignore[assignment]
            print(f"LAN-only mode: allowing clients in {allowed_network}")
    except ValueError:
        print("Warning: Invalid --cidr; disabling LAN-only check.")
        allowed_network = None

    try:
        while True:
            conn, addr = sock.accept()
            client_ip, _client_port = addr
            if allowed_network is not None:
                try:
                    client_ip_obj = ipaddress.ip_address(client_ip)
                    if client_ip_obj not in allowed_network:
                        try:
                            conn.close()
                        finally:
                            continue
                except ValueError:
                    try:
                        conn.close()
                    finally:
                        continue
            asyncio.run(handle_client(conn, box))
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()


@cli.command('start-ws-bridge')
@click.option('--tcp-host', default='127.0.0.1', help='TCP server host to bridge to')
@click.option('--tcp-port', type=int, default=9001, help='TCP server port to bridge to')
@click.option('--ws-host', default='127.0.0.1', help='WebSocket server host to bind')
@click.option('--ws-port', type=int, default=9002, help='WebSocket server port to bind')
def start_ws_bridge(tcp_host: str, tcp_port: int, ws_host: str, ws_port: int) -> None:
    """Start a WebSocket bridge that forwards to a local TCP server."""
    async def handle_ws_client(websocket, path):
        try:
            # Connect to the local TCP server
            tcp_sock = socket.create_connection((tcp_host, tcp_port), timeout=5)
            print(f"WebSocket client connected, bridging to {tcp_host}:{tcp_port}")
            
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
        print(f"WebSocket bridge listening on {ws_host}:{ws_port} -> {tcp_host}:{tcp_port}")
        async with websockets.serve(handle_ws_client, ws_host, ws_port):
            await asyncio.Future()  # run forever
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bridge stopped")


@cli.command()
@click.option('--store', type=click.Path(path_type=Path), required=True)
@click.option('--password', prompt=True, hide_input=True)
@click.option('--host', default='127.0.0.1')
@click.option('--port', type=int, default=9001)
@click.option('--peer-key', required=True, help='Peer base64 public key')
@click.option('--message', default='hello from client')
@click.option('--ws-url', help='WebSocket URL (e.g., wss://6cebd2e1.loca.lt) - overrides host/port')
def connect(store: Path, password: str, host: str, port: int, peer_key: str, message: str, ws_url: str | None) -> None:
    """Connect to a peer and send an encrypted message."""
    priv, _sign, _pub = load_keys(store, password)
    peer = PublicKey(b64d(peer_key))
    box = Box(priv, peer)

    if ws_url:
        # WebSocket connection
        async def ws_connect():
            try:
                # Convert https:// to wss://
                if ws_url.startswith('https://'):
                    ws_url_clean = ws_url.replace('https://', 'wss://')
                elif ws_url.startswith('http://'):
                    ws_url_clean = ws_url.replace('http://', 'ws://')
                else:
                    ws_url_clean = ws_url
                
                print(f"Connecting via WebSocket to {ws_url_clean}")
                async with websockets.connect(ws_url_clean) as websocket:
                    ct = box.encrypt(message.encode('utf-8'))
                    await websocket.send(ct)
                    data = await websocket.recv()
                    pt = box.decrypt(data)
                    print(f"Reply: {pt.decode('utf-8', 'ignore')}")
            except Exception as e:
                print(f"WebSocket connection failed: {e}")
        
        asyncio.run(ws_connect())
    else:
        # TCP connection
        sock = socket.create_connection((host, port), timeout=5)
        with sock:
            ct = box.encrypt(message.encode('utf-8'))
            sock.sendall(ct)
            data = sock.recv(4096)
            pt = box.decrypt(data)
            print(f"Reply: {pt.decode('utf-8', 'ignore')}")


if __name__ == '__main__':
    cli()
