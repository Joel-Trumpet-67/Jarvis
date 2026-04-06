"""
media.py — Media control via WM_APPCOMMAND sent directly to Spotify.

Uses dedicated PLAY (46) and PAUSE (47) commands instead of the
PLAY_PAUSE toggle (14) — Spotify Store sometimes ignores the toggle
but responds to the explicit commands.

No broadcast layer — sending to both direct and broadcast caused
double-triggers that cancelled each other out.
"""

import ctypes
import ctypes.wintypes
import time

_user32 = ctypes.windll.user32

_WM_APPCOMMAND          = 0x0319
_APPCOMMAND_NEXT        = 11
_APPCOMMAND_PREV        = 12
_APPCOMMAND_STOP        = 13
_APPCOMMAND_PLAY_PAUSE  = 14   # toggle — kept as fallback
_APPCOMMAND_VOLUME_MUTE = 8
_APPCOMMAND_VOLUME_DOWN = 9
_APPCOMMAND_VOLUME_UP   = 10
_APPCOMMAND_PLAY        = 46   # explicit play
_APPCOMMAND_PAUSE       = 47   # explicit pause

_KEYEVENTF_KEYUP     = 0x0002
_VK_MEDIA_NEXT       = 0xB0
_VK_MEDIA_PREV       = 0xB1
_VK_MEDIA_STOP       = 0xB2
_VK_MEDIA_PLAY_PAUSE = 0xB3
_VK_VOLUME_MUTE      = 0xAD
_VK_VOLUME_DOWN      = 0xAE
_VK_VOLUME_UP        = 0xAF


def _find_spotify() -> int | None:
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


def _send(cmd: int, vk_fallback: int | None = None):
    """
    Send WM_APPCOMMAND to Spotify directly.
    No broadcast — that caused double-triggers.
    Falls back to virtual key only if Spotify window not found.
    """
    lParam = ctypes.wintypes.LPARAM(cmd << 16)
    hwnd = _find_spotify()
    if hwnd:
        _user32.SendMessageW(hwnd, _WM_APPCOMMAND, hwnd, lParam)
    elif vk_fallback:
        _vk_press(vk_fallback)


# ── Public commands ──────────────────────────────────────────────────────────

def play(_: dict) -> str:
    _send(_APPCOMMAND_PLAY, _VK_MEDIA_PLAY_PAUSE)
    return "Playing."

def pause(_: dict) -> str:
    _send(_APPCOMMAND_PAUSE, _VK_MEDIA_PLAY_PAUSE)
    return "Paused."

def play_pause(_: dict) -> str:
    _send(_APPCOMMAND_PLAY_PAUSE, _VK_MEDIA_PLAY_PAUSE)
    return "Play/pause."

def next_track(_: dict) -> str:
    _send(_APPCOMMAND_NEXT, _VK_MEDIA_NEXT)
    return "Next track."

def prev_track(_: dict) -> str:
    _send(_APPCOMMAND_PREV, _VK_MEDIA_PREV)
    return "Previous track."

def stop_media(_: dict) -> str:
    _send(_APPCOMMAND_STOP, _VK_MEDIA_STOP)
    return "Stopped."

def volume_up(_: dict) -> str:
    for _ in range(3):
        _send(_APPCOMMAND_VOLUME_UP, _VK_VOLUME_UP)
    return "Volume up."

def volume_down(_: dict) -> str:
    for _ in range(3):
        _send(_APPCOMMAND_VOLUME_DOWN, _VK_VOLUME_DOWN)
    return "Volume down."

def mute(_: dict) -> str:
    _send(_APPCOMMAND_VOLUME_MUTE, _VK_VOLUME_MUTE)
    return "Muted."
