# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[ 
     
        ('C:/Users/Joumongo/AppData/Local/Programs/Python/Python311/Lib/site-packages/matplotlib/mpl-data', 'mpl-data'),

      
        ('C:/Users/Joumongo/AppData/Local/Programs/Python/Python311/Lib/site-packages/torch', 'torch'),
    ],
    datas=[('db', 'db'), ('*.ui', '.')], 
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.uic',
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends.backend_qt5agg',
        'torch',
        'torchvision',
        'openpyxl',
        'numpy',
        'pandas'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Economystique',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)