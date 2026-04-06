"""
media.py — Media key control via ctypes.

Sends virtual key events for the standard media keys Windows supports.
Works globally — no need to focus Spotify or any other app.
"""

import ctypes
import time

_KEYEVENTF_KEYUP    = 0x0002

_VK_MEDIA_NEXT      = 0xB0
_VK_MEDIA_PREV      = 0xB1
_VK_MEDIA_STOP      = 0xB2
_VK_MEDIA_PLAY_PAUSE= 0xB3
_VK_VOLUME_MUTE     = 0xAD
_VK_VOLUME_DOWN     = 0xAE
_VK_VOLUME_UP       = 0xAF


def _press(vk: int):
    ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(vk, 0, _KEYEVENTF_KEYUP, 0)


def next_track(_: dict) -> str:
    _press(_VK_MEDIA_NEXT)
    return "Next track."

def prev_track(_: dict) -> str:
    _press(_VK_MEDIA_PREV)
    return "Previous track."

def play_pause(_: dict) -> str:
    _press(_VK_MEDIA_PLAY_PAUSE)
    return "Play/pause."

def stop_media(_: dict) -> str:
    _press(_VK_MEDIA_STOP)
    return "Stopped."

def volume_up(_: dict) -> str:
    for _ in range(3):
        _press(_VK_VOLUME_UP)
    return "Volume up."

def volume_down(_: dict) -> str:
    for _ in range(3):
        _press(_VK_VOLUME_DOWN)
    return "Volume down."

def mute(_: dict) -> str:
    _press(_VK_VOLUME_MUTE)
    return "Muted."
