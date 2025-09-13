import { contextBridge } from "electron";
const api = {
  // Add any custom APIs here
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
