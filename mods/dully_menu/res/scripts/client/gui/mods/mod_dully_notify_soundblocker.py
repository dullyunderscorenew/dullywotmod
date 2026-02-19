
# ------------------------------------------------------------
# Imports
# ------------------------------------------------------------
import traceback

try:
    from messenger_common_chat2 import BATTLE_CHAT_COMMANDS_BY_NAMES
except Exception:
    BATTLE_CHAT_COMMANDS_BY_NAMES = {}
    print("[DULLY] WARNUNG: BATTLE_CHAT_COMMANDS_BY_NAMES konnte nicht importiert werden, möglicherweise inkompatible WoT-Version")

# AvatarChatKeyHandling importieren (Name der Klasse wie im Client)
try:
    from avatar_components.avatar_chat_key_handling import AvatarChatKeyHandling
except Exception:
    AvatarChatKeyHandling = None
    print("[DULLY] WARNUNG: AvatarChatKeyHandling konnte nicht importiert werden, möglicherweise inkompatible WoT-Version")


# ------------------------------------------------------------
# Variablen
# ------------------------------------------------------------
BANNED_NOTIFICATIONS = {
    'ibc_ping_retreat',          # Rückzug
    'ibc_ping_attention',        # Aufmerksamkeit / ständiges Pingen
    'ibc_ping_help_me_ex',       # Hilfe Ping
    'ibc_ping_reply',
    'ibc_ping_help_me_ex_reply',
}



# ------------------------------------------------------------
# Hilfsfunktion: Liste aller bekannten Notifications ins Log schreiben
# ------------------------------------------------------------
def dump_all_notifications():
    try:
        print('[DULLY] ==== Verfügbare Chat Notifications ====')
        for name, data in BATTLE_CHAT_COMMANDS_BY_NAMES.items():
            # data kann None sein in manchen Builds
            sn = getattr(data, 'soundNotification', None)
            sr = getattr(data, 'soundNotificationReply', None)
            print('[DULLY] CommandName:', name)
            print('       soundNotification:', sn)
            print('       soundNotificationReply:', sr)
        print('[DULLY] ==== Ende ====')
    except Exception:
        print('[DULLY] Fehler beim Dumping der Notifications')
        traceback.print_exc()



# ------------------------------------------------------------
# Die Hook-Implementation (überschreibt die Originalmethode)
# Originalsignature: def __playSoundNotification(self, notification, sndPos=None, enableVoice=True, isSentByPlayer=True)
# ------------------------------------------------------------
def install_hook():
    if AvatarChatKeyHandling is None:
        print('[DULLY] AvatarChatKeyHandling nicht gefunden — Hook installation abgebrochen')
        return

    mangled_name = '_AvatarChatKeyHandling__playSoundNotification'
    
    if not hasattr(AvatarChatKeyHandling, mangled_name):
        print('[DULLY] Methode', mangled_name, 'nicht gefunden in AvatarChatKeyHandling')
        return

    original = getattr(AvatarChatKeyHandling, mangled_name)

    def hooked(self, notification, sndPos=None, enableVoice=True, isSentByPlayer=True):
        try:
            if notification is None:
                baseName = None
            else:
                # Remove suffix if present
                try:
                    baseName = notification.replace('_npc', '')
                except Exception:
                    baseName = notification

            print('[DULLY] Notification erhalten:')
            print('       raw =', notification)
            print('       base =', baseName)
            print('       sentByPlayer =', isSentByPlayer)
            print('       enableVoice =', enableVoice)

            # Falls baseName in BANNED -> komplett unterdrücken (kein Voice, kein FX)
            if baseName is not None and baseName in BANNED_NOTIFICATIONS:
                print('[DULLY] >>> BLOCKIERT:', notification)
                # komplett blockieren:
                return

            # sonst Original ausführen
            return original(self, notification, sndPos, enableVoice, isSentByPlayer)

        except Exception:
            print('[DULLY] Fehler im Hook!')
            traceback.print_exc()
            # Bei Fehler Original aufrufen, falls möglich
            try:
                return original(self, notification, sndPos, enableVoice, isSentByPlayer)
            except Exception:
                pass

    # Überschreiben der Methode in der Klasse
    try:
        setattr(AvatarChatKeyHandling, mangled_name, hooked)
        print('[DULLY] Hook auf', mangled_name, 'erfolgreich installiert.')
    except Exception:
        print('[DULLY] Fehler beim Setzen des Hooks!')
        traceback.print_exc()

# ------------------------------------------------------------
# Auto-Initialisierung beim Import der Datei
# ------------------------------------------------------------
print('[DULLY] messages.py importiert — versuche Hook zu installieren')
#dump_all_notifications()
install_hook()
print('[DULLY] messages.py: Initialisierung abgeschlossen')
