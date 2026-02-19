from __future__ import print_function
# -------------------------
# modul-name fuer debug
# -------------------------
_MOD = '[DULLY_SOUNDBLOCKER]'
print(_MOD, 'Starte Initialisierung...')


# -------------------------
# imports
# -------------------------
try: 
   
    import os, json, BigWorld, traceback, ResMgr
    from messenger_common_chat2 import BATTLE_CHAT_COMMANDS_BY_NAMES
    from avatar_components.avatar_chat_key_handling import AvatarChatKeyHandling
except Exception:
    print(_MOD, 'fehler beim importieren; mod wird nicht geladen')
    raise


# -------------------------
# config pfad 
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
print(_MOD, 'config =', _SETTINGS_PATH)

# -------------------------
# notifications sammeln
# -------------------------
def _build_all_notifications():
    names = []
    try:
        for name, data in BATTLE_CHAT_COMMANDS_BY_NAMES.items():
            d_sound = getattr(data, 'soundNotification', None)
            d_sreply = getattr(data, 'soundNotificationReply', None)
            if d_sound and d_sound not in names:
                names.append(d_sound)
            if d_sreply and d_sreply not in names:
                names.append(d_sreply)
    except Exception:
        pass
    # defaults
    defaults = ['ibc_ping_retreat', 
                'ibc_ping_attention',
                'ibc_ping_help_me_ex', 
                'ibc_ping_request', 
                'ibc_ping_reply', 
                'ibc_ping_thanks']
    for d in defaults:
        if d not in names:
            names.append(d)
    return names

ALL_NOTIFICATIONS = _build_all_notifications()

# -------------------------
# defaults blocked
# -------------------------
_DEFAULT_BLOCKED = {
    'ibc_ping_retreat': True,
    'ibc_ping_attention': True,
    'ibc_ping_help_me_ex': True
}

BANNED = {}
_pending_changes = False

# -------------------------
# load / save config
# -------------------------
def load_settings():
    global BANNED, _pending_changes
    try:
        BANNED = {option: False for option in ALL_NOTIFICATIONS}
        for option, wert in _DEFAULT_BLOCKED.items():
            if option in BANNED:
                BANNED[option] = bool(wert)
        if not os.path.isdir(_CONFIG_DIR):
            os.makedirs(_CONFIG_DIR)
        if os.path.isfile(_SETTINGS_PATH):
            try:
                # oeffne datei mit read
                with open(_SETTINGS_PATH, 'r') as datei:
                    data = json.load(datei)
                for option, wert in data.items():
                    if option in BANNED:
                        BANNED[option] = bool(wert)
                _pending_changes = False
                print(_MOD, 'Einstellungen geladen von:', _SETTINGS_PATH)
            except Exception:
                print(_MOD, 'Fehler beim Parsen der Einstellungsdatei; Standardwerte verwendet')
                traceback.print_exc()
        else:
            print(_MOD, 'Keine Einstellungsdatei gefunden; Standardwerte verwendet und gespeichert')
            save_settings()
    except Exception:
        print(_MOD, 'Fehler beim Laden der Einstellungen')
        traceback.print_exc()

def save_settings():
    global _pending_changes
    try:
        if not os.path.isdir(_CONFIG_DIR):
            os.makedirs(_CONFIG_DIR)
        # oeffne datei mit write
        with open(_SETTINGS_PATH, 'w') as datei:    
            # ident=2: rueckt zeilen ein, sort_keys=true: sortiert die keys alphabetisch 
            json.dump(BANNED, datei, indent=2, sort_keys=True)
        _pending_changes = False
        print(_MOD, 'Einstellungen gespeichert nach:', _SETTINGS_PATH)
    except Exception:
        print(_MOD, 'Fehler beim Speichern der Einstellungen')
        traceback.print_exc()

# def set_notification_enabled_runtime(name, enabled):
#     global _pending_changes
#     if name not in BANNED:
#         print(_MOD, 'Unbekannter Notification-Name:', name)
#         return
#     BANNED[name] = not bool(enabled)
#     _pending_changes = True
#     print(_MOD, 'Runtime: %s ist jetzt %s' % (name, 'BLOCKIERT' if BANNED[name] else 'ERLAUBT'))

# -------------------------
# Hook: AvatarChatKeyHandling.__playSoundNotification
# -------------------------

def init_hook_soundblocker():
    mangled = '_AvatarChatKeyHandling__playSoundNotification'
    original = getattr(AvatarChatKeyHandling, mangled)

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
            return original(self, notification, sndPos, enableVoice, isSentByPlayer)
    try:
        setattr(AvatarChatKeyHandling, mangled, hooked)
        print(_MOD, 'Hook installiert auf', mangled)
    except Exception:
        print(_MOD, 'Fehler beim Setzen des Hooks')
        traceback.print_exc()

# -------------------------
# Initialisierung
# -------------------------
load_settings()
init_hook_soundblocker()
print(_MOD, 'Initialisierung abgeschlossen')

# Convenience-API exposed for console usage
__all__ = ['set_notification_enabled_runtime', 'save_settings', 'load_settings', 'ALL_NOTIFICATIONS', 'BANNED']
