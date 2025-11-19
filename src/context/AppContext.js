import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import { useAuth } from './AuthContext';

const AppContext = createContext();

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  const { executeCommand, user } = useAuth();

  // State management
  const [contacts, setContacts] = useState([]);
  const [connections, setConnections] = useState([]);
  const [messages, setMessages] = useState({});
  const [activeChat, setActiveChat] = useState(null);
  const [serverStatus, setServerStatus] = useState('stopped'); // 'stopped', 'starting', 'running'
  const [serverPort, setServerPort] = useState(9001);
  const [connectionInfo, setConnectionInfo] = useState({ directIP: null, tunnelURL: null });
  const [notifications, setNotifications] = useState([]);
  const [sidebarTab, setSidebarTab] = useState('chats'); // 'chats', 'contacts', 'settings'
  const [groups, setGroups] = useState([]);
  const [activeGroup, setActiveGroup] = useState(null);
  const [activeCalls, setActiveCalls] = useState([]);
  const [incomingCalls, setIncomingCalls] = useState([]);
  const [activeVoiceCall, setActiveVoiceCall] = useState(null);

  // Use ref to track previous connections to detect new ones
  const previousConnectionsRef = useRef([]);

  // Contacts management
  const loadContacts = useCallback(async () => {
    if (!user) return;

    try {
      const result = await executeCommand('get_contacts');
      if (result.success) {
        setContacts(result.contacts || []);
      }
    } catch (error) {
      console.error('Failed to load contacts:', error);
    }
  }, [executeCommand, user]);

  const addContact = useCallback(async (contactData) => {
    try {
      const result = await executeCommand('add_contact', contactData);
      if (result.success) {
        await loadContacts(); // Reload contacts
        return { success: true };
      } else {
        return { success: false, error: result.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }, [executeCommand, loadContacts]);

  const removeContact = useCallback(async (username) => {
    try {
      const result = await executeCommand('remove_contact', { username });
      if (result.success) {
        await loadContacts(); // Reload contacts
        // If this contact was the active chat, clear it
        if (activeChat === username) {
          setActiveChat(null);
        }
        return { success: true };
      } else {
        return { success: false, error: result.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }, [executeCommand, loadContacts, activeChat]);

  // Connection management
  const startServer = useCallback(async (port = serverPort) => {
    setServerStatus('starting');

    try {
      const result = await executeCommand('start_server', { port });
      if (result.success) {
        setServerStatus('running');
        setServerPort(port);
        // Update direct IP connection info
        setConnectionInfo(prev => ({
          ...prev,
          directIP: `localhost:${port}`
        }));
        addNotification('Server started successfully', 'success');
        return { success: true };
      } else {
        setServerStatus('stopped');
        return { success: false, error: result.error };
      }
    } catch (error) {
      setServerStatus('stopped');
      return { success: false, error: error.message };
    }
  }, [executeCommand, serverPort]);

  const stopServer = useCallback(async () => {
    setServerStatus('stopping');

    try {
      const result = await executeCommand('stop_server');
      if (result.success) {
        setServerStatus('stopped');
        // Clear all connections when server stops
        setConnections([]);
        // Clear connection info
        setConnectionInfo({ directIP: null, tunnelURL: null });
        addNotification('Server stopped successfully', 'info');
        return { success: true };
      } else {
        setServerStatus('running'); // Revert if stop failed
        return { success: false, error: result.error };
      }
    } catch (error) {
      setServerStatus('running'); // Revert if stop failed
      return { success: false, error: error.message };
    }
  }, [executeCommand]);

  const createTunnel = useCallback(async () => {
    if (serverStatus !== 'running') {
      return { success: false, error: 'Server must be running to create tunnel' };
    }

    try {
      const result = await executeCommand('create_tunnel', { port: serverPort });
      if (result.success && result.tunnel_url) {
        setConnectionInfo(prev => ({
          ...prev,
          tunnelURL: result.tunnel_url
        }));
        addNotification('Tunnel created successfully', 'success');
        return { success: true, tunnel_url: result.tunnel_url };
      } else {
        return { success: false, error: result.error || 'Failed to create tunnel' };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }, [executeCommand, serverPort, serverStatus]);

  const closeTunnel = useCallback(async () => {
    try {
      const result = await executeCommand('close_tunnel', { port: serverPort });
      if (result.success) {
        setConnectionInfo(prev => ({
          ...prev,
          tunnelURL: null
        }));
        addNotification('Tunnel closed successfully', 'info');
        return { success: true };
      } else {
        return { success: false, error: result.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }, [executeCommand, serverPort]);

  const getConnectionInfo = useCallback(async () => {
    if (serverStatus !== 'running') {
      return { success: false, error: 'Server is not running' };
    }

    try {
      const result = await executeCommand('get_connection_info', { port: serverPort });
      if (result.success) {
        setConnectionInfo({
          directIP: result.direct_ip || `localhost:${serverPort}`,
          tunnelURL: result.tunnel_url || null
        });
        return { success: true, connection_info: result };
      } else {
        return { success: false, error: result.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }, [executeCommand, serverPort, serverStatus]);

  const connectToPeer = useCallback(async (peerData) => {
    try {
      const result = await executeCommand('connect_to_peer', peerData);
      if (result.success) {
        // Update connections list
        const newConnection = {
          peer_username: peerData.peer_username,
          status: 'connected',
          connected_at: new Date().toISOString(),
        };
        setConnections(prev => [...prev.filter(c => c.peer_username !== peerData.peer_username), newConnection]);
        addNotification(`Connected to ${peerData.peer_username}`, 'success');
        return { success: true };
      } else {
        return { success: false, error: result.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }, [executeCommand]);

  const loadConnections = useCallback(async () => {
    if (!user) return;

    try {
      const result = await executeCommand('get_connections');
      if (result.success) {
        const newConnections = result.connections || [];
        const previousConnections = previousConnectionsRef.current;

        setConnections(newConnections);

        // Check if we have new connections that might have added contacts
        const newConnectionUsernames = newConnections.map(c => c.peer_username);
        const previousConnectionUsernames = previousConnections.map(c => c.peer_username);

        // If there are new connections, reload contacts to pick up auto-added ones
        const hasNewConnections = newConnectionUsernames.some(username =>
          !previousConnectionUsernames.includes(username)
        );

        if (hasNewConnections) {
          console.log('New connections detected, reloading contacts...');
          loadContacts();
        }

        // Update the ref with current connections
        previousConnectionsRef.current = newConnections;
      }
    } catch (error) {
      console.error('Failed to load connections:', error);
    }
  }, [executeCommand, user, loadContacts]);

  const disconnectPeer = useCallback(async (peerUsername) => {
    try {
      const result = await executeCommand('disconnect_peer', { peer_username: peerUsername });
      if (result.success) {
        setConnections(prev => prev.filter(c => c.peer_username !== peerUsername));
        addNotification(`Disconnected from ${peerUsername}`, 'info');
        return { success: true };
      } else {
        return { success: false, error: result.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }, [executeCommand]);

  // Messaging
  const sendMessage = useCallback(async (peerUsername, messageText) => {
    try {
      const result = await executeCommand('send_message', {
        peer_username: peerUsername,
        message: messageText,
      });

      if (result.success) {
        // Add message to local state
        const newMessage = {
          id: Date.now().toString(),
          text: messageText,
          timestamp: new Date().toISOString(),
          sender: user.username,
          type: 'sent',
        };

        setMessages(prev => ({
          ...prev,
          [peerUsername]: [...(prev[peerUsername] || []), newMessage],
        }));

        return { success: true };
      } else {
        return { success: false, error: result.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }, [executeCommand, user]);

  // Notifications
  const addNotification = useCallback((message, type = 'info', duration = 5000) => {
    const notification = {
      id: Date.now().toString(),
      message,
      type,
      timestamp: new Date().toISOString(),
    };

    setNotifications(prev => [...prev, notification]);

    // Auto-remove notification after duration
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== notification.id));
    }, duration);
  }, []);

  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  // Chat management
  const openChat = useCallback((username) => {
    setActiveChat(username);
    setSidebarTab('chats');

    // Initialize message array if it doesn't exist
    if (!messages[username]) {
      setMessages(prev => ({
        ...prev,
        [username]: [],
      }));
    }
  }, [messages]);

  const closeChat = useCallback(() => {
    setActiveChat(null);
  }, []);

  // Load initial data when user changes
  useEffect(() => {
    if (user) {
      loadContacts();
      loadConnections(); // Also load connections when user logs in
    } else {
      // Clear data when user logs out
      setContacts([]);
      setConnections([]);
      setMessages({});
      setActiveChat(null);
      setServerStatus('stopped');
    }
  }, [user, loadContacts]);

  // Function to check for pending messages
  const checkPendingMessages = useCallback(async () => {
    if (!user) return;

    try {
      const result = await executeCommand('get_pending_messages');
      if (result.success && result.messages && result.messages.length > 0) {
        result.messages.forEach(msg => {
          // Handle group messages separately
          if (msg.is_group) {
            const newMessage = {
              id: Date.now().toString() + Math.random(),
              text: msg.message,
              timestamp: msg.timestamp,
              sender: msg.peer_username,
              sender_id: msg.peer_id,
              type: 'received',
              group_id: msg.group_id,
              group_name: msg.group_name
            };

            setMessages(prev => ({
              ...prev,
              [`group_${msg.group_id}`]: [...(prev[`group_${msg.group_id}`] || []), newMessage],
            }));
          } else {
            const newMessage = {
              id: Date.now().toString() + Math.random(),
              text: msg.message,
              timestamp: msg.timestamp,
              sender: msg.peer_username,
              type: 'received',
            };

            setMessages(prev => ({
              ...prev,
              [msg.peer_username]: [...(prev[msg.peer_username] || []), newMessage],
            }));
          }
        });
      }
    } catch (error) {
      console.error('Failed to check pending messages:', error);
    }
  }, [executeCommand, user]);

  // Periodically update connections and check for messages
  useEffect(() => {
    if (!user) return;

    const interval = setInterval(() => {
      loadConnections();
      checkPendingMessages();
    }, 2000); // Check every 2 seconds to reduce load

    return () => clearInterval(interval);
  }, [user, loadConnections, checkPendingMessages]);

  // Group management
  const loadGroups = useCallback(async () => {
    if (!user) return;

    try {
      const result = await executeCommand('get_groups');
      if (result.success) {
        setGroups(result.groups || []);
      }
    } catch (error) {
      console.error('Failed to load groups:', error);
    }
  }, [executeCommand, user]);

  const createGroup = useCallback(async (name, members, description) => {
    try {
      const result = await executeCommand('create_group', { name, members, description });
      if (result.success) {
        await loadGroups(); // Reload groups
        addNotification(`Group "${name}" created successfully`, 'success');
        return { success: true, group: result.group };
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      addNotification(`Failed to create group: ${error.message}`, 'error');
      throw error;
    }
  }, [executeCommand, loadGroups, addNotification]);

  const sendGroupMessage = useCallback(async (groupId, messageText) => {
    try {
      const result = await executeCommand('send_group_message', {
        group_id: groupId,
        message: messageText,
      });

      if (result.success) {
        // Add message to local state
        const newMessage = {
          id: Date.now().toString(),
          text: messageText,
          timestamp: new Date().toISOString(),
          sender: user.username,
          sender_id: user.user_id,
          type: 'sent',
        };

        setMessages(prev => ({
          ...prev,
          [`group_${groupId}`]: [...(prev[`group_${groupId}`] || []), newMessage],
        }));

        return { success: true, delivered: result.delivered, total: result.total };
      } else {
        return { success: false, error: result.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }, [executeCommand, user]);

  const openGroup = useCallback((groupId) => {
    setActiveGroup(groupId);
    setActiveChat(null); // Clear active chat if opening a group
    setSidebarTab('chats');

    // Initialize message array if it doesn't exist
    if (!messages[`group_${groupId}`]) {
      setMessages(prev => ({
        ...prev,
        [`group_${groupId}`]: [],
      }));
    }
  }, [messages]);

  const closeGroup = useCallback(() => {
    setActiveGroup(null);
  }, []);

  // Load groups when user logs in
  useEffect(() => {
    if (user) {
      loadGroups();
    } else {
      setGroups([]);
      setActiveGroup(null);
    }
  }, [user, loadGroups]);

  // Voice call management
  const startVoiceCall = useCallback(async (peerId) => {
    try {
      const result = await executeCommand('start_voice_call', { peer_id: peerId });
      if (result.success) {
        addNotification('Starting voice call...', 'info');
        // The call will be added to activeCalls when we poll
        return { success: true, callId: result.call_id };
      } else {
        addNotification(`Failed to start call: ${result.error}`, 'error');
        return { success: false, error: result.error };
      }
    } catch (error) {
      addNotification(`Error starting call: ${error.message}`, 'error');
      return { success: false, error: error.message };
    }
  }, [executeCommand, addNotification]);

  const acceptVoiceCall = useCallback(async (callId) => {
    try {
      const result = await executeCommand('accept_voice_call', { call_id: callId });
      if (result.success) {
        // Remove from incoming calls
        setIncomingCalls(prev => prev.filter(c => c.call_id !== callId));
        addNotification('Call connected', 'success');
        return { success: true };
      } else {
        addNotification(`Failed to accept call: ${result.error}`, 'error');
        return { success: false, error: result.error };
      }
    } catch (error) {
      addNotification(`Error accepting call: ${error.message}`, 'error');
      return { success: false, error: error.message };
    }
  }, [executeCommand, addNotification]);

  const rejectVoiceCall = useCallback(async (callId) => {
    try {
      const result = await executeCommand('reject_voice_call', { call_id: callId });
      // Remove from incoming calls regardless of result
      setIncomingCalls(prev => prev.filter(c => c.call_id !== callId));

      if (result.success) {
        return { success: true };
      } else {
        return { success: false, error: result.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }, [executeCommand]);

  const endVoiceCall = useCallback(async (callId) => {
    try {
      const result = await executeCommand('end_voice_call', { call_id: callId });
      if (result.success) {
        setActiveVoiceCall(null);
        addNotification('Call ended', 'info');
        return { success: true };
      } else {
        return { success: false, error: result.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }, [executeCommand, addNotification]);

  const checkPendingCalls = useCallback(async () => {
    if (!user) return;

    try {
      const result = await executeCommand('get_pending_calls', {});
      if (result.success && result.calls && result.calls.length > 0) {
        setIncomingCalls(prev => {
          // Add new calls, avoid duplicates
          const newCalls = result.calls.filter(
            newCall => !prev.some(existingCall => existingCall.call_id === newCall.call_id)
          );
          return [...prev, ...newCalls];
        });
      }
    } catch (error) {
      console.error('Failed to check pending calls:', error);
    }
  }, [executeCommand, user]);

  const loadActiveCalls = useCallback(async () => {
    if (!user) return;

    try {
      const result = await executeCommand('get_active_calls');
      if (result.success) {
        setActiveCalls(result.calls || []);

        // Update active voice call if there's an active call
        const activeCall = (result.calls || []).find(c => c.status === 'active');
        if (activeCall) {
          setActiveVoiceCall(activeCall);
        } else if (activeCalls.length === 0) {
          setActiveVoiceCall(null);
        }
      }
    } catch (error) {
      console.error('Failed to load active calls:', error);
    }
  }, [executeCommand, user, activeCalls.length]);

  // Poll for pending calls and active calls
  useEffect(() => {
    if (!user) return;

    const interval = setInterval(() => {
      checkPendingCalls();
      loadActiveCalls();
    }, 2000); // Check every 2 seconds

    return () => clearInterval(interval);
  }, [user, checkPendingCalls, loadActiveCalls]);

  const value = {
    // State
    contacts,
    connections,
    messages,
    activeChat,
    serverStatus,
    serverPort,
    connectionInfo,
    notifications,
    sidebarTab,

    // Actions
    addContact,
    removeContact,
    loadContacts,
    startServer,
    stopServer,
    createTunnel,
    closeTunnel,
    getConnectionInfo,
    connectToPeer,
    disconnectPeer,
    sendMessage,
    addNotification,
    removeNotification,
    openChat,
    closeChat,
    setSidebarTab,
    setServerPort,

    // Groups
    groups,
    activeGroup,
    loadGroups,
    createGroup,
    sendGroupMessage,
    openGroup,
    closeGroup,

    // Voice calls
    activeCalls,
    incomingCalls,
    activeVoiceCall,
    startVoiceCall,
    acceptVoiceCall,
    rejectVoiceCall,
    endVoiceCall,

    // User context
    currentUser: user,
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};