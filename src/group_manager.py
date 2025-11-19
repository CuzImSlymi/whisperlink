import os
import json
import uuid
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import asdict

from models import Group

class GroupManager:
    """Manages groups and their members"""
    
    def __init__(self, data_dir: str = ".whisperlink", user_id: str = None):
        self.data_dir = data_dir
        self.user_id = user_id
        
        if user_id:
            # Create user-specific directory
            self.user_data_dir = os.path.join(data_dir, user_id)
            os.makedirs(self.user_data_dir, exist_ok=True)
            self.groups_file = os.path.join(self.user_data_dir, "groups.json")
        else:
            # Should not happen in normal operation as groups are user-specific (or shared?)
            # For P2P, each user tracks the groups they are in.
            # Synchronization is a harder problem, but for MVP we'll assume 
            # group info is shared via messages.
            self.groups_file = os.path.join(data_dir, "groups.json")
            
        self.groups: Dict[str, Group] = self._load_groups()
    
    def _load_groups(self) -> Dict[str, Group]:
        """Load groups from file"""
        if not os.path.exists(self.groups_file):
            return {}
        
        try:
            with open(self.groups_file, 'r') as f:
                data = json.load(f)
                return {gid: Group(**group_data) for gid, group_data in data.items()}
        except:
            return {}
    
    def _save_groups(self):
        """Save groups to file"""
        data = {gid: asdict(group) for gid, group in self.groups.items()}
        with open(self.groups_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_group(self, name: str, members: List[str], description: str = None) -> Group:
        """Create a new group"""
        group_id = str(uuid.uuid4())
        
        # Ensure current user is in members if not already
        if self.user_id and self.user_id not in members:
            members.append(self.user_id)
            
        group = Group(
            group_id=group_id,
            name=name,
            members=members,
            created_at=datetime.now().isoformat(),
            admin_id=self.user_id,
            description=description
        )
        
        self.groups[group_id] = group
        self._save_groups()
        return group
    
    def add_group(self, group: Group):
        """Add an existing group (e.g. joined from invite)"""
        self.groups[group.group_id] = group
        self._save_groups()
        
    def get_group(self, group_id: str) -> Optional[Group]:
        """Get a group by ID"""
        return self.groups.get(group_id)
    
    def list_groups(self) -> List[Group]:
        """List all groups"""
        return list(self.groups.values())
    
    def add_member(self, group_id: str, member_id: str) -> bool:
        """Add a member to a group"""
        group = self.groups.get(group_id)
        if group:
            if member_id not in group.members:
                group.members.append(member_id)
                self._save_groups()
                return True
        return False
    
    def remove_member(self, group_id: str, member_id: str) -> bool:
        """Remove a member from a group"""
        group = self.groups.get(group_id)
        if group:
            if member_id in group.members:
                group.members.remove(member_id)
                self._save_groups()
                return True
        return False
        
    def delete_group(self, group_id: str) -> bool:
        """Delete a group"""
        if group_id in self.groups:
            del self.groups[group_id]
            self._save_groups()
            return True
        return False
