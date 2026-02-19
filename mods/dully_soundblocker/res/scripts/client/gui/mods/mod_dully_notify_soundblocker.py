# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import json
import traceback

# -------------------------
# Modul-Header
# -------------------------
_MOD = '[DULLY]'
print(_MOD, 'mod_dully_soundblocker importiert — init')

# -------------------------
# CONFIG Pfad (robust)
# -------------------------
def _get_mods_root():
    try:
        # versuche Pfad über paths.xml (wie im Client üblich)
        root = _openSection('../paths.xml')['Paths'].values()[0].asString
        modsroot = os.path.join(root, 'mods')
        if os.path.isdir(modsroot):
            return modsroot
        return root
    except Exception:
        # Fallback: relative Pfad "mods" (res_mods/res/.. kann variieren)
        guess = os.path.join(os.getcwd(), 'mods')
        return guess

_MODS_ROOT = _get_mods_root()
_CONFIG_DIR = os.path.join(_MODS_ROOT, 'configs', 'dully')
_SETTINGS_PATH = os.path.join(_CONFIG_DIR, 'dully_soundblocker_settings.json')
print(_MOD, 'Config dir =', _CONFIG_DIR)

# -------------------------
# Notifications discovery
# -------------------------
try:
    from messenger_common_chat2 import BATTLE_CHAT_COMMANDS_BY_NAMES
except Exception:
    BATTLE_CHAT_COMMANDS_BY_NAMES = {}

def _build_all_notifications():
    names = []
    try:
        for name, data in BATTLE_CHAT_COMMANDS_BY_NAMES.items():
            sn = getattr(data, 'soundNotification', None)
            sr = getattr(data, 'soundNotificationReply', None)
            if sn and sn not in names:
                names.append(sn)
            if sr and sr not in names:
                names.append(sr)
    except Exception:
        pass
    # Ergänze mit einer kleinen, sinnvollen Default-Liste
    defaults = ['ibc_ping_retreat', 'ibc_ping_attention',
                'ibc_ping_help_me_ex', 'ibc_ping_request', 'ibc_ping_reply', 'ibc_ping_thanks']
    for d in defaults:
        if d not in names:
            names.append(d)
    return names

ALL_NOTIFICATIONS = _build_all_notifications()

# -------------------------
# Default blocked (initial)
# -------------------------
_DEFAULT_BLOCKED = {
    'ibc_ping_retreat': True,
    'ibc_ping_attention': True,
    'ibc_ping_help_me_ex': True
}

# runtime mapping: True == BLOCKIERT
BANNED = {}
_pending_changes = False

# -------------------------
# load / save
# -------------------------
def load_settings():
    global BANNED, _pending_changes
    try:
        BANNED = {n: False for n in ALL_NOTIFICATIONS}
        for k, v in _DEFAULT_BLOCKED.items():
            if k in BANNED:
                BANNED[k] = bool(v)
        if not os.path.isdir(_CONFIG_DIR):
            try:
                os.makedirs(_CONFIG_DIR)
            except Exception:
                pass
        if os.path.isfile(_SETTINGS_PATH):
            try:
                with open(_SETTINGS_PATH, 'r') as f:
                    data = json.load(f)
                for k, v in data.items():
                    if k in BANNED:
                        BANNED[k] = bool(v)
                _pending_changes = False
                print(_MOD, 'Einstellungen geladen von:', _SETTINGS_PATH)
            except Exception:
                print(_MOD, 'Fehler beim Parsen der Einstellungsdatei; Standardwerte verwendet')
                traceback.print_exc()
        else:
            print(_MOD, 'Keine Einstellungsdatei gefunden; Standardwerte verwendet')
    except Exception:
        print(_MOD, 'Fehler beim Laden der Einstellungen')
        traceback.print_exc()

def save_settings():
    global _pending_changes
    try:
        if not os.path.isdir(_CONFIG_DIR):
            os.makedirs(_CONFIG_DIR)
        with open(_SETTINGS_PATH, 'w') as f:
            json.dump(BANNED, f, indent=2, sort_keys=True)
        _pending_changes = False
        print(_MOD, 'Einstellungen gespeichert nach:', _SETTINGS_PATH)
    except Exception:
        print(_MOD, 'Fehler beim Speichern der Einstellungen')
        traceback.print_exc()

def set_notification_enabled_runtime(name, enabled):
    """ enabled=True bedeutet: ERLAUBT (nicht geblockt).
        Wir speichern intern als BANNED[name] = not enabled """
    global _pending_changes
    if name not in BANNED:
        print(_MOD, 'Unbekannter Notification-Name:', name)
        return
    BANNED[name] = not bool(enabled)
    _pending_changes = True
    print(_MOD, 'Runtime: %s ist jetzt %s' % (name, 'BLOCKIERT' if BANNED[name] else 'ERLAUBT'))

# -------------------------
# Hook: AvatarChatKeyHandling.__playSoundNotification
# -------------------------
try:
    from avatar_components.avatar_chat_key_handling import AvatarChatKeyHandling
    _HAS_AVATAR = True
except Exception:
    AvatarChatKeyHandling = None
    _HAS_AVATAR = False

def install_playSound_hook():
    if not _HAS_AVATAR or AvatarChatKeyHandling is None:
        print(_MOD, 'AvatarChatKeyHandling nicht gefunden — Hook wird nicht installiert')
        return
    mangled = '_AvatarChatKeyHandling__playSoundNotification'
    if not hasattr(AvatarChatKeyHandling, mangled):
        print(_MOD, 'Methode %s nicht vorhanden in AvatarChatKeyHandling' % mangled)
        return
    try:
        original = getattr(AvatarChatKeyHandling, mangled)
    except Exception:
        print(_MOD, 'Kann Originalmethode nicht bekommen')
        return

    def hooked(self, notification, sndPos=None, enableVoice=True, isSentByPlayer=True):
        try:
            base = notification.replace('_npc', '') if notification else None
            print(_MOD, 'Notification erhalten: raw=%s base=%s sentByPlayer=%s enableVoice=%s' %
                  (str(notification), str(base), str(bool(isSentByPlayer)), str(bool(enableVoice))))
            if base and BANNED.get(base, False):
                print(_MOD, '>>> BLOCKIERT:', base)
                return
            return original(self, notification, sndPos, enableVoice, isSentByPlayer)
        except Exception:
            print(_MOD, 'Fehler im Hook; rufe Original auf')
            traceback.print_exc()
            try:
                return original(self, notification, sndPos, enableVoice, isSentByPlayer)
            except Exception:
                return None

    try:
        setattr(AvatarChatKeyHandling, mangled, hooked)
        print(_MOD, 'Hook installiert auf', mangled)
    except Exception:
        print(_MOD, 'Fehler beim Setzen des Hooks')
        traceback.print_exc()

# -------------------------
# Settings UI integration (sicherer Weg)
# - 1) erweitere SettingsParams.getFeedbackSettings (nur Anzeige)
# - 2) intercept SettingsWindow._applySettings um DULLY keys herauszufiltern und selbst zu speichern
# -------------------------
try:
    from gui.Scaleform.daapi.view.common.settings.SettingsParams import SettingsParams
    _HAS_SETTINGSPARAMS = True
except Exception:
    SettingsParams = None
    _HAS_SETTINGSPARAMS = False

try:
    from gui.Scaleform.daapi.view.common.settings.SettingsWindow import SettingsWindow
    _HAS_SETTINGSWINDOW = True
except Exception:
    SettingsWindow = None
    _HAS_SETTINGSWINDOW = False

# patch SettingsParams.getFeedbackSettings: füge Gruppe 'DULLY_SOUND_BLOCKER' ein (Anzeige)
if _HAS_SETTINGSPARAMS and SettingsParams is not None:
    try:
        _orig_getFeedback = SettingsParams.getFeedbackSettings

        def _dully_getFeedbackSettings(self):
            data = _orig_getFeedback(self)
            # dully_container: mapping notif_name -> { 'value': <bool allowed>, 'default': <bool> }
            dully_container = {}
            for n in ALL_NOTIFICATIONS:
                dully_container[n] = {'value': (not BANNED.get(n, False)), 'default': True}
            # Insert with a unique key. UI zeigt keys as sections.
            data['DULLY_SOUND_BLOCKER'] = dully_container
            # Debug
            print(_MOD, 'SettingsParams.getFeedbackSettings erweitert (DULLY_SOUND_BLOCKER)')
            return data

        SettingsParams.getFeedbackSettings = _dully_getFeedbackSettings
    except Exception:
        print(_MOD, 'Fehler beim Patchen von SettingsParams.getFeedbackSettings')
        traceback.print_exc()
else:
    print(_MOD, 'SettingsParams nicht verfügbar — UI-Integration übersprungen')

# patch SettingsWindow._applySettings: entferne DULLY keys aus diff und handle sie selbst
if _HAS_SETTINGSWINDOW and SettingsWindow is not None:
    try:
        _orig__applySettings = SettingsWindow._applySettings

        def _dully__applySettings(self, settings, isCloseWnd):
            # settings ist ein dict; prüfe auf DULLY_SOUND_BLOCKER Key
            try:
                if isinstance(settings, dict) and 'DULLY_SOUND_BLOCKER' in settings:
                    try:
                        dully_section = settings.pop('DULLY_SOUND_BLOCKER')
                        # dully_section erwartet mapping notif -> value (bool) OR {notif: value} depending on frontend
                        # handle both shapes: if nested dicts, try to get values
                        for notif, val in dully_section.items():
                            # val könnte dict {'value': True} oder True/False
                            if isinstance(val, dict):
                                # frontend sendet typischerweise { 'value': True }
                                v = val.get('value', val.get('default', True))
                            else:
                                v = val
                            # v == True means ALLOWED -> BANNED = not v
                            BANNED[notif] = not bool(v)
                        # persist immediately
                        save_settings()
                        print(_MOD, 'DULLY_SETTINGS angewendet und gespeichert')
                    except Exception:
                        print(_MOD, 'Fehler beim Anwenden der DULLY Sektion')
                        traceback.print_exc()
                # now call original with filtered settings
            except Exception:
                traceback.print_exc()
            # finally call original method (works with remaining settings)
            try:
                return _orig__applySettings(self, settings, isCloseWnd)
            except Exception:
                print(_MOD, 'Fehler im originalen _applySettings nach DULLY-Handling')
                traceback.print_exc()
        SettingsWindow._applySettings = _dully__applySettings
        print(_MOD, 'SettingsWindow._applySettings gepatcht (DULLY interception)')
    except Exception:
        print(_MOD, 'Fehler beim Patchen von SettingsWindow._applySettings')
        traceback.print_exc()
else:
    print(_MOD, 'SettingsWindow nicht verfügbar — apply-interception übersprungen')

# -------------------------
# Initialisierung
# -------------------------
load_settings()
install_playSound_hook()
print(_MOD, 'Initialisierung abgeschlossen')

# Convenience-API exposed for console usage
__all__ = ['set_notification_enabled_runtime', 'save_settings', 'load_settings', 'ALL_NOTIFICATIONS', 'BANNED']
