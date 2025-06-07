# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('static', 'static'),  # 包含静态文件（HTML, CSS, JS）
        ('check.ico', '.'),    # 包含图标文件
    ],
    hiddenimports=[
        'pandas',
        'openpyxl',  # pandas读取Excel文件需要
        'xlrd',      # 支持旧版Excel文件
        'win32com.client',
        'pywintypes',
        'pythoncom',
        'webview',   # pywebview核心模块
        'webview.platforms.winforms',  # Windows平台支持
        'webview.platforms.edgechromium',  # Edge WebView2支持
        'webview.platforms.mshtml',  # 备用渲染器
        'webview.js',  # JavaScript API支持
        'webview.util',  # 工具模块
        'threading',
        'json',
        'datetime',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',  # 排除不需要的大型库
        'numpy.testing',
        'scipy',
        'tkinter',     # 如果不使用tkinter，可以排除
        'PyQt5',       # 排除其他GUI框架
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Check list',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为False隐藏控制台窗口，GUI应用不需要控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='check.ico',  # 设置应用程序图标
)
