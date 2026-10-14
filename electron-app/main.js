const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');
const config = require('./config.json');

const isDev = process.argv.includes('--dev');
const examUrl = process.env.EXAM_URL || config.examUrl;
const allowedOrigin = new URL(examUrl).origin;

function createWindow() {
  const win = new BrowserWindow({
    kiosk: !isDev,
    fullscreen: !isDev,
    width: 1280,
    height: 800,
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      devTools: isDev,
    },
  });

  // Сервер по этому суффиксу отличает киоск-клиент от обычного браузера.
  win.webContents.setUserAgent(`${win.webContents.getUserAgent()} ExamKiosk/0.1`);

  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));

  win.webContents.on('will-navigate', (event, url) => {
    if (new URL(url).origin !== allowedOrigin) event.preventDefault();
  });

  win.webContents.on('context-menu', (event) => event.preventDefault());

  win.loadURL(examUrl);
}

Menu.setApplicationMenu(null);

app.whenReady().then(createWindow);

app.on('window-all-closed', () => app.quit());
