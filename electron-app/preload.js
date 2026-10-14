const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('examKiosk', { version: '0.1.0' });
