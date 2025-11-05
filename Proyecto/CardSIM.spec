# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=['e:\\Universidad\\Quinto\\TFG_CE\\Proyecto'],
    binaries=[],
    datas=[
        ('assets/icons/*', 'assets/icons'),
        ('assets/teoria/*', 'assets/teoria'),
    ],
    hiddenimports=[
        'src.gui.interface',
        'src.gui.dialogs', 
        'src.gui.physical_card_dialogs',
        'src.gui.create_card_dialog',
        'src.gui.card_explorer',
        'src.core.memory_manager',
        'src.core.apdu_handler',
        'src.core.card_session',
        'src.core.session_manager',
        'src.core.physical_card_handler',
        'src.core.code_improvements',
        'src.utils.constants',
        'src.utils.app_states',
        'src.utils.resource_manager'
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
    name='CardSIM',
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
    icon='assets/icons/etsisi_multi.ico',
    entitlements_file=None,
)
