import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const projectRoot = path.resolve(__dirname, '../../..');

console.log('🚀 Preparing Clarity for release...\n');

// Step 1: Install dependencies
console.log('📦 Installing dependencies...');
try {
  execSync('npm install', { 
    cwd: path.join(projectRoot, 'apps', 'desktop'),
    stdio: 'inherit' 
  });
  console.log('✅ Dependencies installed\n');
} catch (error) {
  console.error('❌ Failed to install dependencies:', error.message);
  process.exit(1);
}

// Step 2: Check if models exist
console.log('🤖 Checking models...');
const modelsPath = path.join(projectRoot, 'models');
if (!fs.existsSync(modelsPath)) {
  console.log('⚠️  Models directory not found. Creating placeholder...');
  fs.mkdirSync(modelsPath, { recursive: true });
  fs.mkdirSync(path.join(modelsPath, 'face'), { recursive: true });
  
  // Create placeholder files
  fs.writeFileSync(path.join(modelsPath, 'face', 'README.txt'), 
    'Place your ONNX models here:\n- detector_retinaface.onnx\n- arcface_resnet100.onnx\n- align_5pts.json');
}
console.log('✅ Models checked\n');

// Step 3: Check data directory
console.log('💾 Checking data directory...');
const dataPath = path.join(projectRoot, 'data');
if (!fs.existsSync(dataPath)) {
  console.log('📁 Creating data directory...');
  fs.mkdirSync(dataPath, { recursive: true });
  fs.mkdirSync(path.join(dataPath, 'index'), { recursive: true });
}
console.log('✅ Data directory ready\n');

// Step 4: Create icon if missing
console.log('🎨 Checking icon...');
const iconPath = path.join(__dirname, '..', 'build', 'icon.ico');
if (!fs.existsSync(iconPath)) {
  console.log('🖼️  Creating placeholder icon...');
  const buildDir = path.dirname(iconPath);
  if (!fs.existsSync(buildDir)) {
    fs.mkdirSync(buildDir, { recursive: true });
  }
  
  // Copy favicon as placeholder icon
  const faviconPath = path.join(__dirname, '..', 'public', 'favicon.ico');
  if (fs.existsSync(faviconPath)) {
    fs.copyFileSync(faviconPath, iconPath);
    console.log('✅ Icon created from favicon\n');
  } else {
    console.log('⚠️  No favicon found, skipping icon creation\n');
  }
}

console.log('🎉 Clarity is ready for building!');
console.log('\nNext steps:');
console.log('1. Run: npm run build:win (for Windows executable)');
console.log('2. Check the dist/ folder for your executable');
console.log('3. Test the executable before your demo\n');
