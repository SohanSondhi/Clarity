import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const projectRoot = path.resolve(__dirname, '../../..');
const apiPath = path.join(projectRoot, 'apps', 'api');
const pyinstallerSpec = path.join(projectRoot, 'installer', 'win', 'exe', 'pyinstaller.spec');
const outputDir = path.join(__dirname, '..', 'resources', 'python-backend');

console.log('Building Python backend...');
console.log('Project root:', projectRoot);
console.log('API path:', apiPath);
console.log('PyInstaller spec:', pyinstallerSpec);
console.log('Output directory:', outputDir);

// Ensure output directory exists
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

// Check if PyInstaller is available
function checkPyInstaller() {
  return new Promise((resolve, reject) => {
    const child = spawn('pyinstaller', ['--version'], { stdio: 'pipe' });
    child.on('close', (code) => {
      if (code === 0) {
        resolve(true);
      } else {
        reject(new Error('PyInstaller not found. Please install it with: pip install pyinstaller'));
      }
    });
    child.on('error', (err) => {
      reject(new Error('PyInstaller not found. Please install it with: pip install pyinstaller'));
    });
  });
}

// Build with PyInstaller
function buildWithPyInstaller() {
  return new Promise((resolve, reject) => {
    console.log('Running PyInstaller...');
    const child = spawn('pyinstaller', [
      pyinstallerSpec,
      '--distpath', outputDir,
      '--workpath', path.join(outputDir, 'build'),
      '--clean'
    ], {
      cwd: apiPath,
      stdio: 'inherit'
    });

    child.on('close', (code) => {
      if (code === 0) {
        console.log('Python backend built successfully!');
        resolve();
      } else {
        reject(new Error(`PyInstaller failed with code ${code}`));
      }
    });

    child.on('error', (err) => {
      reject(new Error(`Failed to run PyInstaller: ${err.message}`));
    });
  });
}

// Copy Python source as fallback
function copyPythonSource() {
  console.log('Copying Python source as fallback...');
  const srcPath = path.join(apiPath, 'src');
  const destPath = path.join(outputDir, 'src');
  
  // Only copy if source exists
  if (!fs.existsSync(srcPath)) {
    console.log('⚠️  API source not found at:', srcPath);
    return;
  }
  
  // Simple recursive copy function
  function copyRecursive(src, dest) {
    if (!fs.existsSync(dest)) {
      fs.mkdirSync(dest, { recursive: true });
    }
    
    const items = fs.readdirSync(src);
    for (const item of items) {
      const srcItem = path.join(src, item);
      const destItem = path.join(dest, item);
      
      if (fs.statSync(srcItem).isDirectory()) {
        copyRecursive(srcItem, destItem);
      } else {
        fs.copyFileSync(srcItem, destItem);
      }
    }
  }
  
  copyRecursive(srcPath, destPath);
  
  // Copy requirements or pyproject.toml
  const pyprojectPath = path.join(apiPath, 'pyproject.toml');
  if (fs.existsSync(pyprojectPath)) {
    fs.copyFileSync(pyprojectPath, path.join(outputDir, 'pyproject.toml'));
  }
  
  console.log('Python source copied successfully!');
}

// Main build process
async function main() {
  try {
    // Always copy source as fallback
    copyPythonSource();
    
    // Try to build with PyInstaller if available
    try {
      await checkPyInstaller();
      await buildWithPyInstaller();
    } catch (error) {
      console.warn('PyInstaller build failed, using source copy:', error.message);
      console.log('The application will run Python from source.');
    }
    
    console.log('Python backend preparation complete!');
  } catch (error) {
    console.error('Failed to prepare Python backend:', error.message);
    process.exit(1);
  }
}

main();
