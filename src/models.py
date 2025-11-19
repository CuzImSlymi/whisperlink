from dataclasses import dataclass, asdict
from typing import Optional, List

@dataclass
class User:
    user_id: str
    username: str
    password_hash: str
    private_key: str
    public_key: str
    created_at: str
    last_login: Optional[str] = None

@dataclass 
class Contact:
    user_id: str
    username: str
    public_key: str
    connection_type: str  # "direct" or "tunnel"
    address: Optional[str] = None  # IP address for direct connections
    tunnel_url: Optional[str] = None  # Tunnel URL for tunneled connections
    added_at: str = ""
    last_seen: Optional[str] = None

@dataclass
class Connection:
    peer_id: str
    peer_username: str
    connection_type: str
    address: str
    port: int
    status: str  # "connecting", "connected", "disconnected"
    established_at: Optional[str] = None
    socket_obj: Optional[object] = None
    websocket_obj: Optional[object] = None

@dataclass
class Group:
    group_id: str
    name: str
    members: List[str]  # List of user_ids
    created_at: str
    admin_id: str
    description: Optional[str] = None
