import { app, shell, BrowserWindow } from 'electron'
import { join } from 'path'
import { spawn, ChildProcess } from 'child_process'
import { existsSync } from 'fs'

let pythonProcess: ChildProcess | null = null

async function startPythonBackend(): Promise<void> {
  const isDev = process.env.NODE_ENV === 'development'
  
  if (isDev) {
    console.log('Development mode: Python backend should be started separately')
    return
  }

  try {
    const resourcesPath = process.resourcesPath
    const pythonBackendPath = join(resourcesPath, 'python-backend')
    
    // Try to find the built executable first
    const exePath = join(pythonBackendPath, 'clarity-api', 'clarity-api.exe')
    
    if (existsSync(exePath)) {
      console.log('Starting Python backend from executable:', exePath)
      pythonProcess = spawn(exePath, [], {
        cwd: pythonBackendPath,
        stdio: 'pipe'
      })
    } else {
      // Fallback to running from source
      const srcPath = join(pythonBackendPath, 'src')
      const mainPath = join(srcPath, 'clarity_api', 'main.py')
      
      if (existsSync(mainPath)) {
        console.log('Starting Python backend from source:', mainPath)
        pythonProcess = spawn('python', ['-m', 'clarity_api.main'], {
          cwd: srcPath,
          stdio: 'pipe',
          env: { ...process.env, PYTHONPATH: srcPath }
        })
      } else {
        console.warn('Python backend not found, app will use mock data')
        return // Don't throw error, just continue without backend
      }
    }

    if (pythonProcess) {
      pythonProcess.stdout?.on('data', (data) => {
        console.log('Python Backend:', data.toString())
      })

      pythonProcess.stderr?.on('data', (data) => {
        console.error('Python Backend Error:', data.toString())
      })

      pythonProcess.on('close', (code) => {
        console.log(`Python backend exited with code ${code}`)
        pythonProcess = null
      })

      pythonProcess.on('error', (error) => {
        console.error('Failed to start Python backend:', error)
        pythonProcess = null
      })

      // Wait a moment for the backend to start
      await new Promise(resolve => setTimeout(resolve, 2000))
    }
  } catch (error) {
    console.error('Error starting Python backend:', error)
  }
}

function stopPythonBackend(): void {
  if (pythonProcess) {
    console.log('Stopping Python backend...')
    pythonProcess.kill()
    pythonProcess = null
  }
}

function createWindow(): void {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, 'preload.js'),
      sandbox: false,
      nodeIntegration: false,
      contextIsolation: true
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // HMR for renderer base on electron-vite cli.
  // Load the remote URL for development or the local html file for production.
  if (process.env.NODE_ENV === 'development' && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../index.html'))
  }
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(async () => {
  // Set app user model id for windows
  app.setAppUserModelId('com.clarity.desktop')

  // Start Python backend first
  await startPythonBackend()

  createWindow()

  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  stopPythonBackend()
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  stopPythonBackend()
})

// In this file you can include the rest of your app"s main process
// code. You can also put them in separate files and require them here.
