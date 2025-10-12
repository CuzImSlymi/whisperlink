import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
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
    } else {
      // Clear data when user logs out
      setContacts([]);
      setConnections([]);
      setMessages({});
      setActiveChat(null);
      setServerStatus('stopped');
    }
  }, [user, loadContacts]);

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
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};