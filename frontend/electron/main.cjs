const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')

const isDev = !app.isPackaged

const JWC_LOGIN_URL = 'https://authserver.jxust.edu.cn/authserver/login?service=' +
  encodeURIComponent('https://jw.jxust.edu.cn/jsxsd/')

const COURSE_DETECT_SCRIPT = `(() => {
  const compactText = (doc) => ((doc.body && doc.body.innerText) || '')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 20000)

  const frames = []
  for (const frame of Array.from(document.querySelectorAll('iframe'))) {
    try {
      const doc = frame.contentDocument || frame.contentWindow.document
      if (doc && doc.documentElement) {
        frames.push({
          url: frame.src || doc.location.href || '',
          title: doc.title || '',
          text: compactText(doc),
          html: doc.documentElement.outerHTML,
        })
      }
    } catch (_err) {}
  }

  const page = {
    url: location.href,
    title: document.title || '',
    text: compactText(document),
    html: document.documentElement.outerHTML,
  }
  const candidates = [page, ...frames]
  const detected = candidates.some((item) => {
    const text = item.text || ''
    const url = item.url || ''
    const looksLikeScheduleUrl = /xskb|kb|kbcx|course|schedule/i.test(url)
    const hasScheduleWord = text.includes('\u8bfe\u8868') || text.includes('\u8bfe\u7a0b\u8868') || text.includes('\u6211\u7684\u8bfe\u8868')
    const hasGridWord = text.includes('\u661f\u671f') || text.includes('\u5468\u4e00') || text.includes('\u7b2c\u4e00\u5927\u8282') || text.includes('\u8282\u6b21')
    const hasCourseDetail = text.includes('\u4e0a\u8bfe\u5730\u70b9') || text.includes('\u4efb\u8bfe\u6559\u5e08') || text.includes('\u6559\u5e08') || text.includes('\u6559\u5ba4')
    return (looksLikeScheduleUrl && (hasScheduleWord || hasGridWord || hasCourseDetail)) || (hasScheduleWord && hasGridWord)
  })

  return {
    detected,
    source_url: page.url,
    title: page.title,
    html: page.html,
    frames: frames.map(({ url, title, html }) => ({ url, title, html })),
  }
})()`

function openCourseImportWindow() {
  return new Promise((resolve, reject) => {
    const parent = BrowserWindow.getFocusedWindow() || BrowserWindow.getAllWindows()[0]
    const importWin = new BrowserWindow({
      width: 1120,
      height: 780,
      minWidth: 900,
      minHeight: 620,
      title: 'Import Course Schedule',
      parent,
      modal: false,
      backgroundColor: '#080604',
      webPreferences: {
        contextIsolation: true,
        nodeIntegration: false,
        sandbox: true,
      },
    })

    let settled = false
    let pollTimer = null
    let timeoutTimer = null

    const cleanup = () => {
      if (pollTimer) clearInterval(pollTimer)
      if (timeoutTimer) clearTimeout(timeoutTimer)
      pollTimer = null
      timeoutTimer = null
    }

    const finish = (fn, value, closeWindow = true) => {
      if (settled) return
      settled = true
      cleanup()
      if (closeWindow && !importWin.isDestroyed()) importWin.close()
      fn(value)
    }

    const pollPage = async () => {
      if (settled || importWin.isDestroyed()) return
      try {
        const result = await importWin.webContents.executeJavaScript(COURSE_DETECT_SCRIPT, true)
        if (result && result.detected) {
          finish(resolve, result)
        }
      } catch (_err) {
        // Navigation may be mid-flight; the next poll will try again.
      }
    }

    importWin.webContents.on('did-finish-load', () => {
      setTimeout(pollPage, 800)
    })

    importWin.on('closed', () => {
      finish(reject, new Error('Import window was closed before a schedule page was detected'), false)
    })

    timeoutTimer = setTimeout(() => {
      finish(reject, new Error('Import timed out. Please log in to JWC and open the visible schedule page'))
    }, 300000)

    pollTimer = setInterval(pollPage, 1500)
    importWin.loadURL(JWC_LOGIN_URL)
  })
}

function registerIpcHandlers() {
  ipcMain.handle('courses:browser-import', () => openCourseImportWindow())
}


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

app.whenReady().then(() => {
  registerIpcHandlers()
  createWindow()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})
