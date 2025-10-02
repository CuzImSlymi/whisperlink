const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Python backend communication
  executePythonCommand: (command, args) => 
    ipcRenderer.invoke('python-command', command, args),
  
  // Window controls
  minimize: () => ipcRenderer.invoke('window-minimize'),
  maximize: () => ipcRenderer.invoke('window-maximize'),
  close: () => ipcRenderer.invoke('window-close'),
  
  // System info
  platform: process.platform,
  
  // Events
  onWindowStateChange: (callback) => 
    ipcRenderer.on('window-state-changed', callback),
  
  removeAllListeners: (channel) => 
    ipcRenderer.removeAllListeners(channel)
});