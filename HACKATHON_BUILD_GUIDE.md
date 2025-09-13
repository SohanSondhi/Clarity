# 🚀 Clarity - Hackathon Build Guide

This guide will help you create a standalone executable for your Clarity application for the hackathon.

## 📋 Prerequisites

1. **Node.js** (v18 or higher) - for the Electron frontend
2. **Python** (v3.8 or higher) - for the FastAPI backend
3. **PyInstaller** (optional, for better performance):
   ```bash
   pip install pyinstaller
   ```

## 🎯 Quick Build (Recommended for Hackathon)

### Option 1: One-Click Build (Windows)
```bash
# From the project root
.\build-clarity.bat
```

### Option 2: Manual Build
```bash
# Navigate to desktop app
cd apps/desktop

# Install dependencies
npm install

# Build the executable
npm run build:release
```

## 📁 Output Files

After building, you'll find these files in `apps/desktop/dist/`:

- **`Clarity Setup.exe`** - Windows installer (recommended for demos)
- **`win-unpacked/`** - Portable executable folder
  - Run `win-unpacked/Clarity.exe` directly without installation

## 🧪 Testing Your Executable

1. **Install and run** the setup file OR run the portable version
2. **Verify the app starts** and shows the file explorer interface
3. **Test basic functionality**:
   - Browse folders
   - Search files
   - Check if the Python backend starts automatically

## 🔧 What the Build Process Does

1. **Prepares Python Backend**: 
   - Tries to create a PyInstaller executable for better performance
   - Falls back to bundling Python source code if PyInstaller isn't available

2. **Bundles Electron App**:
   - Compiles the React/TypeScript frontend
   - Packages everything with Electron
   - Creates Windows installer and portable version

3. **Includes Dependencies**:
   - AI models (face detection, etc.)
   - Vector indexes and data
   - Configuration files

## 🐛 Troubleshooting

### Build Fails
- Ensure all dependencies are installed: `npm install`
- Check Python is available in PATH
- For better results, install PyInstaller: `pip install pyinstaller`

### Executable Won't Start
- Try the portable version in `win-unpacked/` folder
- Check Windows Defender isn't blocking the executable
- Run from command line to see error messages

### Python Backend Issues
- The app includes fallback mock data if the Python backend fails
- Ensure Python dependencies are installed in your development environment
- Check `models/` folder contains required ONNX files

## 📝 Demo Tips

1. **Use the installer version** for a more professional demo
2. **Test thoroughly** before your presentation
3. **Have a backup plan** - the app works with mock data if the backend fails
4. **Prepare sample files** to demonstrate search and indexing features

## 🎬 Demo Script

1. Install and launch Clarity
2. Show the modern file explorer interface
3. Demonstrate file browsing and navigation
4. Search for files using the semantic search
5. Show face recognition features (if models are available)

## 📦 Distribution

- The installer (`Clarity Setup.exe`) is about 200-300MB
- You can distribute just this single file
- No additional installations required for end users

Good luck with your hackathon! 🎉
