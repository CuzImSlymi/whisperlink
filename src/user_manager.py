import os
import json
from typing import Dict, Optional
from datetime import datetime
from dataclasses import asdict

from .models import User
from .crypto_manager import CryptoManager

class UserManager:
    """Manages user registration, login, and user data"""
    
    def __init__(self, data_dir: str = ".whisperlink"):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self.current_user: Optional[User] = None
        self.crypto = CryptoManager()
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Load existing users
        self.users: Dict[str, User] = self._load_users()
    
    def _load_users(self) -> Dict[str, User]:
        """Load users from file"""
        if not os.path.exists(self.users_file):
            return {}
        
        try:
            with open(self.users_file, 'r') as f:
                data = json.load(f)
                return {uid: User(**user_data) for uid, user_data in data.items()}
        except:
            return {}
    
    def _save_users(self):
        """Save users to file"""
        data = {uid: asdict(user) for uid, user in self.users.items()}
        with open(self.users_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register_user(self, username: str, password: str) -> str:
        """Register a new user and return their User ID"""
        import uuid # Moved here to avoid circular dependency with models
        user_id = str(uuid.uuid4()).replace('-', '')
        
        # Check if username already exists
        for user in self.users.values():
            if user.username == username:
                raise ValueError(f"Username '{username}' already exists")
        
        # Generate cryptographic keys
        private_key, public_key = self.crypto.generate_keypair()
        
        # Hash password
        password_hash = self.crypto.hash_password(password)
        
        # Create user
        user = User(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            private_key=private_key,
            public_key=public_key,
            created_at=datetime.now().isoformat()
        )
        
        self.users[user_id] = user
        self._save_users()
        
        return user_id
    
    def login(self, username: str, password: str) -> bool:
        """Login user with username and password"""
        for user in self.users.values():
            if user.username == username:
                if self.crypto.verify_password(password, user.password_hash):
                    self.current_user = user
                    user.last_login = datetime.now().isoformat()
                    self._save_users()
                    return True
                else:
                    return False
        return False
    
    def logout(self):
        """Logout current user"""
        self.current_user = None
    
    def get_current_user(self) -> Optional[User]:
        """Get currently logged in user"""
        return self.current_user
