# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os
import sys
from pathlib import Path

# Get the project root directory
spec_root = os.path.dirname(os.path.abspath(SPEC))
project_root = Path(spec_root).parent.parent.parent
api_path = project_root / "apps" / "api" / "src"
models_path = project_root / "models"

# Add the API source to Python path
sys.path.insert(0, str(api_path))

a = Analysis(
    [str(api_path / "clarity_api" / "main.py")],
    pathex=[str(api_path)],
    binaries=[],
    datas=[
        (str(models_path / "face"), "models/face"),
        (str(project_root / "config"), "config"),
    ],
    hiddenimports=[
        # Core runtime
        'uvicorn',
        'fastapi',

        # Actual routes used in this project
        'clarity_api.routes.tree',
        'clarity_api.routes.rename',
        'clarity_api.routes.refresh',
        'clarity_api.routes.delete',
        'clarity_api.routes.create',
        'clarity_api.routes.index',
        'clarity_api.routes.clear',

        # Indexing / embeddings
        'clarity_api.indexing.image_embed',
        'sentence_transformers',
        'transformers',
        'onnxruntime',
        'torch',
        'PIL',

        # Data & IO stack
        'dotenv',
        'lancedb',
        'pyarrow',
        'pandas',
        'numpy',
        'pdfplumber',
        'docx',
        'bs4',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='clarity-api',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    cofile=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='clarity-api',
)
