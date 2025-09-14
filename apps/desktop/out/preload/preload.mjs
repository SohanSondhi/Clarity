import { contextBridge, ipcRenderer } from "electron";
const api = {
  openPath: (path) => ipcRenderer.invoke("open-path", path)
};
const electronAPI = {
  platform: process.platform
  // Add other APIs as needed
};
if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld("electron", electronAPI);
    contextBridge.exposeInMainWorld("api", api);
  } catch (error) {
    console.error(error);
  }
} else {
  window.electron = electronAPI;
  window.api = api;
}
