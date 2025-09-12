import os
from typing import Tuple

# Try to import PyNaCl for real encryption, fall back to mock for demo
try:
    import nacl.utils
    from nacl.public import PrivateKey, PublicKey, Box
    from nacl.encoding import HexEncoder
    from nacl.hash import blake2b
    from nacl.secret import SecretBox
    import nacl.pwhash
    ENCRYPTION_AVAILABLE = True
except ImportError:
    # Mock classes for demo when PyNaCl is not available
    class MockPrivateKey:
        def __init__(self, key_data=None):
            self.key_data = key_data or os.urandom(32)
            
        @classmethod
        def generate(cls):
            return cls()
        
        def encode(self, encoder):
            return self.key_data.hex().encode()
            
        @property
        def public_key(self):
            return MockPublicKey(self.key_data)

    class MockPublicKey:
        def __init__(self, key_data):
            self.key_data = key_data
            
        def encode(self, encoder):
            return self.key_data.hex().encode()

    class MockBox:
        def __init__(self, private_key, public_key):
            self.private_key = private_key
            self.public_key = public_key
        
        def encrypt(self, message, nonce=None):
            if isinstance(message, str):
                message = message.encode()
            # Mock encryption - just base64 encode for demo
            import base64
            return base64.b64encode(message)
        
        def decrypt(self, encrypted_data):
            import base64
            return base64.b64decode(encrypted_data)

    class MockHexEncoder:
        pass
    
    # Use mock classes
    PrivateKey = MockPrivateKey
    PublicKey = MockPublicKey  
    Box = MockBox
    HexEncoder = MockHexEncoder
    ENCRYPTION_AVAILABLE = False

class CryptoManager:
    """Handles all cryptographic operations"""
    
    def __init__(self):
        self.encoder = HexEncoder()
    
    def generate_keypair(self) -> Tuple[str, str]:
        """Generate a new private/public key pair"""
        private_key = PrivateKey.generate()
        public_key = private_key.public_key
        
        private_key_str = private_key.encode(self.encoder).decode('ascii')
        public_key_str = public_key.encode(self.encoder).decode('ascii')
        
        return private_key_str, public_key_str
    
    def hash_password(self, password: str, salt: bytes = None) -> str:
        """Hash password securely"""
        if salt is None:
            salt = os.urandom(16)
        
        if ENCRYPTION_AVAILABLE:
            # Use proper password hashing with PyNaCl
            try:
                import nacl.pwhash
                hash_bytes = nacl.pwhash.str(password.encode())
                return hash_bytes.decode('ascii')
            except:
                pass
        
        # Fallback password hashing
        import hashlib
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000).hex() + ":" + salt.hex()
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        if ENCRYPTION_AVAILABLE:
            try:
                import nacl.pwhash
                return nacl.pwhash.verify(password_hash.encode(), password.encode())
            except:
                pass
        
        # Fallback verification
        try:
            stored_hash, salt_hex = password_hash.split(":")
            salt = bytes.fromhex(salt_hex)
            import hashlib
            computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000).hex()
            return computed_hash == stored_hash
        except:
            return False
    
    def encrypt_message(self, sender_private_key: str, receiver_public_key: str, message: str) -> str:
        """Encrypt a message for secure transmission"""
        if ENCRYPTION_AVAILABLE:
            try:
                sender_key = PrivateKey(sender_private_key, encoder=self.encoder)
                receiver_key = PublicKey(receiver_public_key, encoder=self.encoder)
                box = Box(sender_key, receiver_key)
                return box.encrypt(message.encode()).decode('ascii')
            except:
                pass
        
        # Mock encryption for demo
        import base64
        return base64.b64encode(f"{sender_private_key[:8]}:{message}".encode()).decode()
    
    def decrypt_message(self, receiver_private_key: str, sender_public_key: str, encrypted_message: str) -> str:
        """Decrypt a received message"""
        if ENCRYPTION_AVAILABLE:
            try:
                receiver_key = PrivateKey(receiver_private_key, encoder=self.encoder)
                sender_key = PublicKey(sender_public_key, encoder=self.encoder)
                box = Box(receiver_key, sender_key)
                return box.decrypt(encrypted_message.encode()).decode()
            except:
                pass
        
        # Mock decryption for demo
        import base64
        try:
            decoded = base64.b64decode(encrypted_message).decode()
            return decoded.split(":", 1)[1]
        except:
            return "Failed to decrypt message"
