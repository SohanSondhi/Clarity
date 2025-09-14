import { app, BrowserWindow, ipcMain, shell } from "electron";
import { join } from "path";
import { spawn } from "child_process";
import { existsSync } from "fs";
import __cjs_mod__ from "node:module";
const __filename = import.meta.filename;
const __dirname = import.meta.dirname;
const require2 = __cjs_mod__.createRequire(import.meta.url);
let pythonProcess = null;
async function startPythonBackend() {
  const isDev = process.env.NODE_ENV === "development";
  if (isDev) {
    console.log("Development mode: Python backend should be started separately");
    return;
  }
  try {
    const resourcesPath = process.resourcesPath;
    const pythonBackendPath = join(resourcesPath, "python-backend");
    const exePath = join(pythonBackendPath, "clarity-api", "clarity-api.exe");
    if (existsSync(exePath)) {
      console.log("Starting Python backend from executable:", exePath);
      pythonProcess = spawn(exePath, [], {
        cwd: pythonBackendPath,
        stdio: "pipe"
      });
    } else {
      const srcPath = join(pythonBackendPath, "src");
      const mainPath = join(srcPath, "clarity_api", "main.py");
      if (existsSync(mainPath)) {
        console.log("Starting Python backend from source:", mainPath);
        pythonProcess = spawn("python", ["-m", "clarity_api.main"], {
          cwd: srcPath,
          stdio: "pipe",
          env: { ...process.env, PYTHONPATH: srcPath }
        });
      } else {
        console.warn("Python backend not found, app will use mock data");
        return;
      }
    }
    if (pythonProcess) {
      pythonProcess.stdout?.on("data", (data) => {
        console.log("Python Backend:", data.toString());
      });
      pythonProcess.stderr?.on("data", (data) => {
        console.error("Python Backend Error:", data.toString());
      });
      pythonProcess.on("close", (code) => {
        console.log(`Python backend exited with code ${code}`);
        pythonProcess = null;
      });
      pythonProcess.on("error", (error) => {
        console.error("Failed to start Python backend:", error);
        pythonProcess = null;
      });
      await new Promise((resolve) => setTimeout(resolve, 2e3));
    }
  } catch (error) {
    console.error("Error starting Python backend:", error);
  }
}
function stopPythonBackend() {
  if (pythonProcess) {
    console.log("Stopping Python backend...");
    pythonProcess.kill();
    pythonProcess = null;
  }
}
function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, "preload.js"),
      sandbox: false,
      nodeIntegration: false,
      contextIsolation: true
    }
  });
  mainWindow.on("ready-to-show", () => {
    mainWindow.show();
  });
  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url);
    return { action: "deny" };
  });
  if (process.env.NODE_ENV === "development" && process.env["ELECTRON_RENDERER_URL"]) {
    mainWindow.loadURL(process.env["ELECTRON_RENDERER_URL"]);
  } else {
    mainWindow.loadFile(join(__dirname, "../index.html"));
  }
}
app.whenReady().then(async () => {
  app.setAppUserModelId("com.clarity.desktop");
  await startPythonBackend();
  createWindow();
  app.on("activate", function() {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});
app.on("window-all-closed", () => {
  stopPythonBackend();
  if (process.platform !== "darwin") {
    app.quit();
  }
});
app.on("before-quit", () => {
  stopPythonBackend();
});
ipcMain.handle("open-path", async (_event, path) => {
  try {
    await shell.openPath(path);
    return { success: true };
  } catch (e) {
    return { success: false, error: String(e) };
  }
});
