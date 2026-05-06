"""
media.py — Media control via WM_APPCOMMAND sent directly to Spotify.

Windows only. On non-Windows platforms all functions are no-ops that
return a polite message instead of crashing on import.
"""

import sys
import time

_WINDOWS = sys.platform == "win32"

if _WINDOWS:
    import ctypes
    import ctypes.wintypes

    _user32 = ctypes.windll.user32

    _WM_APPCOMMAND          = 0x0319
    _APPCOMMAND_NEXT        = 11
    _APPCOMMAND_PREV        = 12
    _APPCOMMAND_STOP        = 13
    _APPCOMMAND_PLAY_PAUSE  = 14
    _APPCOMMAND_VOLUME_MUTE = 8
    _APPCOMMAND_VOLUME_DOWN = 9
    _APPCOMMAND_VOLUME_UP   = 10
    _APPCOMMAND_PLAY        = 46
    _APPCOMMAND_PAUSE       = 47

    _KEYEVENTF_KEYUP     = 0x0002
    _VK_MEDIA_NEXT       = 0xB0
    _VK_MEDIA_PREV       = 0xB1
    _VK_MEDIA_STOP       = 0xB2
    _VK_MEDIA_PLAY_PAUSE = 0xB3
    _VK_VOLUME_MUTE      = 0xAD
    _VK_VOLUME_DOWN      = 0xAE
    _VK_VOLUME_UP        = 0xAF

    def _find_spotify():
        found = []
        EnumProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM
        )
        def _cb(hwnd, _):
            if not _user32.IsWindowVisible(hwnd):
                return True
            n = _user32.GetWindowTextLengthW(hwnd)
            if n > 0:
                buf = ctypes.create_unicode_buffer(n + 1)
                _user32.GetWindowTextW(hwnd, buf, n + 1)
                if "spotify" in buf.value.lower():
                    found.append(hwnd)
            return True
        _user32.EnumWindows(EnumProc(_cb), 0)
        return found[0] if found else None

    def _vk_press(vk: int):
        _user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.05)
        _user32.keybd_event(vk, 0, _KEYEVENTF_KEYUP, 0)

    def _send(cmd: int, vk_fallback=None):
        lParam = ctypes.wintypes.LPARAM(cmd << 16)
        hwnd = _find_spotify()
        if hwnd:
            _user32.SendMessageW(hwnd, _WM_APPCOMMAND, hwnd, lParam)
        elif vk_fallback:
            _vk_press(vk_fallback)

    def play(_):       _send(_APPCOMMAND_PLAY,        _VK_MEDIA_PLAY_PAUSE); return "Playing."
    def pause(_):      _send(_APPCOMMAND_PAUSE,       _VK_MEDIA_PLAY_PAUSE); return "Paused."
    def play_pause(_): _send(_APPCOMMAND_PLAY_PAUSE,  _VK_MEDIA_PLAY_PAUSE); return "Play/pause."
    def next_track(_): _send(_APPCOMMAND_NEXT,        _VK_MEDIA_NEXT);       return "Next track."
    def prev_track(_): _send(_APPCOMMAND_PREV,        _VK_MEDIA_PREV);       return "Previous track."
    def stop_media(_): _send(_APPCOMMAND_STOP,        _VK_MEDIA_STOP);       return "Stopped."
    def mute(_):       _send(_APPCOMMAND_VOLUME_MUTE, _VK_VOLUME_MUTE);      return "Muted."

    def volume_up(_):
        for _ in range(3):
            _send(_APPCOMMAND_VOLUME_UP, _VK_VOLUME_UP)
        return "Volume up."

    def volume_down(_):
        for _ in range(3):
            _send(_APPCOMMAND_VOLUME_DOWN, _VK_VOLUME_DOWN)
        return "Volume down."

else:
    # Non-Windows — media control not available
    _MSG = "Media control is Windows-only."

    def play(_):        return _MSG
    def pause(_):       return _MSG
    def play_pause(_):  return _MSG
    def next_track(_):  return _MSG
    def prev_track(_):  return _MSG
    def stop_media(_):  return _MSG
    def volume_up(_):   return _MSG
    def volume_down(_): return _MSG
    def mute(_):        return _MSG
