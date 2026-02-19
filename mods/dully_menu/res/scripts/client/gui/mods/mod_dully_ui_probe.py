# -*- coding: utf-8 -*-
# dully_ui_probe.py (einmal ausführen, loggt verfügbare UI-Module)
print('[DULLY_PROBE] UI probe gestartet')

candidates = [
    'frameworks.wulf',
    'frameworks.wulf.window',
    'gui.impl.pub.popover',
    'gui.impl.pub.backport',
    'gui.impl.pub.dialog_window',
    'gui.impl.gen.view_models.views.modals.simple_modal_view_model',
    'gui.impl.gen.view_models.windows.popovers.popover_window_model',
    'gui.impl.gen.view_models.views.modals.simple_modal_view_model',
    'gui.impl.backport',
    'backport',
    'gui.modsListApi',
    'gui.impl.pub.ViewImpl',
    'gui.Scaleform.daapi.view.common',
]

import importlib

for mod in candidates:
    try:
        m = importlib.import_module(mod)
        print('[DULLY_PROBE] import ok:', mod)
        # list some attributes for inspection
        attrs = dir(m)
        print('[DULLY_PROBE]   sample attrs:', ', '.join(attrs[:10]))
    except Exception as e:
        print('[DULLY_PROBE] import failed:', mod, '->', e)

# Versuche einige konkrete helper-objects zu importieren
try:
    from gui.modsListApi import g_modsListApi
    print('[DULLY_PROBE] g_modsListApi available')
    # try introspect methods
    try:
        print('[DULLY_PROBE] g_modsListApi methods:', ', '.join([n for n in dir(g_modsListApi) if not n.startswith('_')]) )
    except Exception:
        pass
except Exception as e:
    print('[DULLY_PROBE] g_modsListApi not available ->', e)

try:
    import frameworks.wulf as w
    print('[DULLY_PROBE] frameworks.wulf available')
    try:
        import frameworks.wulf.window as ww
        print('[DULLY_PROBE] frameworks.wulf.window available')
        print('[DULLY_PROBE] wulf_window attrs:', ', '.join(dir(ww)[:20]))
    except Exception as e:
        print('[DULLY_PROBE] wulf.window import failed ->', e)
except Exception as e:
    print('[DULLY_PROBE] frameworks.wulf not available ->', e)

# try to import backport/popover content classes often present
for name in ('BackportPopOverContent', 'PopOverWindow', 'SimpleToolTipWindow', 'SFWindow'):
    try:
        # attempt from common modules
        from frameworks.wulf.windows_system import window
        print('[DULLY_PROBE] frameworks.wulf.windows_system.window exists; attrs sample:', ', '.join(dir(window)[:10]))
        break
    except Exception:
        pass

print('[DULLY_PROBE] Probe Ende')
