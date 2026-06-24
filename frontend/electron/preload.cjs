const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  minimize: () => ipcRenderer.send('window:minimize'),
  maximize: () => ipcRenderer.send('window:maximize'),
  close: () => ipcRenderer.send('window:close'),
  importCoursesFromJwc: () => ipcRenderer.invoke('courses:browser-import'),
  onMaximizeChange: (cb) => {
    ipcRenderer.on('window:maximize-change', (_e, isMaximized) => cb(isMaximized))
  },
  isElectron: true,
})
