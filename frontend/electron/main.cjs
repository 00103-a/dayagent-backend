const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')

const isDev = !app.isPackaged

// 高分屏（2K/4K/Retina）禁止 Electron 额外缩放，保持像素锐利
app.commandLine.appendSwitch('force-device-scale-factor', '1')

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 680,
    frame: false,
    transparent: true,
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#00000000',
    show: false,
    vibrancy: 'under-window',
    visualEffectState: 'active',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      zoomFactor: 1.0,
    },
  })

  win.once('ready-to-show', () => {
    win.show()
  })

  if (isDev) {
    win.loadURL('http://localhost:3000')
  } else {
    win.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  }

  /* ── Window control IPC ─────────────────────────────────── */
  ipcMain.on('window:minimize', () => win.minimize())
  ipcMain.on('window:maximize', () => {
    if (win.isMaximized()) win.unmaximize()
    else win.maximize()
  })
  ipcMain.on('window:close', () => win.close())

  /* ── Notify renderer of maximize state changes ──────────── */
  win.on('maximize', () => {
    win.webContents.send('window:maximize-change', true)
    win.webContents.executeJavaScript('window.dispatchEvent(new Event("resize"))')
  })
  win.on('unmaximize', () => {
    win.webContents.send('window:maximize-change', false)
    win.webContents.executeJavaScript('window.dispatchEvent(new Event("resize"))')
  })
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})
