# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for TrustLens Backend
This bundles the FastAPI application and all dependencies into a standalone executable.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all Python files from the api directory
api_files = []
for root, dirs, files in os.walk('api'):
    for file in files:
        if file.endswith('.py'):
            full_path = os.path.join(root, file)
            # Get the directory relative to api
            rel_dir = os.path.dirname(os.path.relpath(full_path, 'api'))
            if rel_dir == '.':
                dest_dir = 'api'
            else:
                dest_dir = os.path.join('api', rel_dir)
            api_files.append((full_path, dest_dir))

# Collect data files for transformers (model files)
transformers_datas = collect_data_files('transformers')
torch_datas = collect_data_files('torch')

# Collect all submodules
hidden_imports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'pydantic',
    'httpx',
    'transformers',
    'torch',
    'tldextract',
    'requests',
    'bs4',
    'beautifulsoup4',
]

# Add all submodules from api
for root, dirs, files in os.walk('api'):
    for file in files:
        if file.endswith('.py') and file != '__init__.py':
            module_path = os.path.join(root, file[:-3])
            module_name = module_path.replace(os.sep, '.')
            hidden_imports.append(module_name)

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=api_files + transformers_datas + torch_datas,
    hiddenimports=hidden_imports,
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
    name='trustlens-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
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
    name='trustlens-backend',
)
