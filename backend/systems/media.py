"""
media.py — Media control via WM_APPCOMMAND.

Sends WM_APPCOMMAND directly to the Spotify window — no focus change,
no keybd_event that gets lost to the wrong app. Falls back to the
system-wide media virtual keys if Spotify isn't found.
"""

import ctypes
import ctypes.wintypes
import time

_user32 = ctypes.windll.user32

# WM_APPCOMMAND constants
_WM_APPCOMMAND          = 0x0319
_APPCOMMAND_VOLUME_MUTE = 8
_APPCOMMAND_VOLUME_DOWN = 9
_APPCOMMAND_VOLUME_UP   = 10
_APPCOMMAND_NEXT        = 11
_APPCOMMAND_PREV        = 12
_APPCOMMAND_STOP        = 13
_APPCOMMAND_PLAY_PAUSE  = 14

# Fallback virtual keys (used if no target window found)
_KEYEVENTF_KEYUP     = 0x0002
_VK_MEDIA_NEXT       = 0xB0
_VK_MEDIA_PREV       = 0xB1
_VK_MEDIA_STOP       = 0xB2
_VK_MEDIA_PLAY_PAUSE = 0xB3
_VK_VOLUME_MUTE      = 0xAD
_VK_VOLUME_DOWN      = 0xAE
_VK_VOLUME_UP        = 0xAF


def _find_spotify() -> int | None:
    """Return the Spotify window handle, or None."""
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


_VK_MAP = {
    _APPCOMMAND_NEXT:        _VK_MEDIA_NEXT,
    _APPCOMMAND_PREV:        _VK_MEDIA_PREV,
    _APPCOMMAND_STOP:        _VK_MEDIA_STOP,
    _APPCOMMAND_PLAY_PAUSE:  _VK_MEDIA_PLAY_PAUSE,
    _APPCOMMAND_VOLUME_UP:   _VK_VOLUME_UP,
    _APPCOMMAND_VOLUME_DOWN: _VK_VOLUME_DOWN,
    _APPCOMMAND_VOLUME_MUTE: _VK_VOLUME_MUTE,
}

def _vk_press(vk: int):
    _user32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.05)
    _user32.keybd_event(vk, 0, _KEYEVENTF_KEYUP, 0)


def _appcommand(cmd: int):
    """
    Three-layer approach — each one is tried in order:
    1. WM_APPCOMMAND via SendMessage to Spotify window
    2. Broadcast WM_APPCOMMAND to all top-level windows
    3. keybd_event virtual media key (global fallback)
    """
    lParam = ctypes.wintypes.LPARAM(cmd << 16)

    # Layer 1 — direct to Spotify
    hwnd = _find_spotify()
    if hwnd:
        _user32.SendMessageW(hwnd, _WM_APPCOMMAND, hwnd, lParam)
        time.sleep(0.05)

    # Layer 2 — broadcast to all windows (catches Store/UWP apps)
    HWND_BROADCAST = ctypes.wintypes.HWND(0xFFFF)
    _user32.PostMessageW(HWND_BROADCAST, _WM_APPCOMMAND, 0, lParam)
    time.sleep(0.05)

    # Layer 3 — virtual key fallback
    vk = _VK_MAP.get(cmd)
    if vk:
        _vk_press(vk)


def next_track(_: dict) -> str:
    _appcommand(_APPCOMMAND_NEXT)
    return "Next track."

def prev_track(_: dict) -> str:
    _appcommand(_APPCOMMAND_PREV)
    return "Previous track."

def play_pause(_: dict) -> str:
    _appcommand(_APPCOMMAND_PLAY_PAUSE)
    return "Play/pause."

def stop_media(_: dict) -> str:
    _appcommand(_APPCOMMAND_STOP)
    return "Stopped."

def volume_up(_: dict) -> str:
    for _ in range(3):
        _appcommand(_APPCOMMAND_VOLUME_UP)
    return "Volume up."

def volume_down(_: dict) -> str:
    for _ in range(3):
        _appcommand(_APPCOMMAND_VOLUME_DOWN)
    return "Volume down."

def mute(_: dict) -> str:
    _appcommand(_APPCOMMAND_VOLUME_MUTE)
    return "Muted."
