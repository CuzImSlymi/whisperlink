import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import asdict

from models import Contact

class ContactManager:
    """Manages contacts and their connection information"""
    
    def __init__(self, data_dir: str = ".whisperlink", user_id: str = None):
        self.data_dir = data_dir
        self.user_id = user_id
        
        if user_id:
            # Create user-specific directory
            self.user_data_dir = os.path.join(data_dir, user_id)
            os.makedirs(self.user_data_dir, exist_ok=True)
            self.contacts_file = os.path.join(self.user_data_dir, "contacts.json")
        else:
            # Global contacts (for backward compatibility)
            self.contacts_file = os.path.join(data_dir, "contacts.json")
            
        self.contacts: Dict[str, Contact] = self._load_contacts()
    
    def _load_contacts(self) -> Dict[str, Contact]:
        """Load contacts from file"""
        if not os.path.exists(self.contacts_file):
            return {}
        
        try:
            with open(self.contacts_file, 'r') as f:
                data = json.load(f)
                return {uid: Contact(**contact_data) for uid, contact_data in data.items()}
        except:
            return {}
    
    def _save_contacts(self):
        """Save contacts to file"""
        data = {uid: asdict(contact) for uid, contact in self.contacts.items()}
        with open(self.contacts_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_contact(self, contact_user_id: str, username: str, public_key: str, 
                   connection_type: str = "direct", address: str = None, 
                   tunnel_url: str = None) -> bool:
        """Add a new contact"""
        # Check if contact already exists by username (more user-friendly)
        for contact in self.contacts.values():
            if contact.username == username:
                return False
        
        contact = Contact(
            user_id=contact_user_id,
            username=username,
            public_key=public_key,
            connection_type=connection_type,
            address=address,
            tunnel_url=tunnel_url,
            added_at=datetime.now().isoformat()
        )
        
        # Use contact_user_id as key for the contact
        self.contacts[contact_user_id] = contact
        self._save_contacts()
        return True
    
    def remove_contact(self, user_id: str) -> bool:
        """Remove a contact by user ID"""
        if user_id in self.contacts:
            del self.contacts[user_id]
            self._save_contacts()
            return True
        return False
    
    def remove_contact_by_username(self, username: str) -> bool:
        """Remove a contact by username"""
        contact_to_remove = None
        for user_id, contact in self.contacts.items():
            if contact.username == username:
                contact_to_remove = user_id
                break
        
        if contact_to_remove:
            del self.contacts[contact_to_remove]
            self._save_contacts()
            return True
        return False
    
    def get_contact(self, user_id: str) -> Optional[Contact]:
        """Get a contact by user ID"""
        return self.contacts.get(user_id)
    
    def list_contacts(self) -> List[Contact]:
        """Get all contacts for this user"""
        return list(self.contacts.values())
    
    def update_contact_last_seen(self, user_id: str):
        """Update last seen time for a contact"""
        if user_id in self.contacts:
            self.contacts[user_id].last_seen = datetime.now().isoformat()
            self._save_contacts()
