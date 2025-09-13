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
        'uvicorn',
        'fastapi',
        'clarity_api.routes.actions',
        'clarity_api.routes.face',
        'clarity_api.routes.index',
        'clarity_api.routes.search',
        'clarity_api.routes.summarize',
        'clarity_api.core.settings',
        'clarity_api.indexing.crawler',
        'clarity_api.search.vector_store',
        'clarity_api.search.vector_store_face',
        'clarity_api.llm.chat_local',
        'clarity_api.multimodal.caption_fallback',
        'sentence_transformers',
        'faiss',
        'onnxruntime',
        'torch',
        'torchvision',
        'PIL',
        'cv2',
        'numpy',
        'pandas',
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
