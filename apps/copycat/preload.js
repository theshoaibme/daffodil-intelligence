const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  isElectron: true,
  closeApp: () => ipcRenderer.send('close-app'),
  setIgnoreMouse: (ignore) => ipcRenderer.send('set-ignore-mouse', ignore),
  getSources: () => ipcRenderer.invoke('get-sources'),
  openExternal: (url) => ipcRenderer.send('open-external', url)
});

