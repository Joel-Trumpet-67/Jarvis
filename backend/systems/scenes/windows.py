"""
windows.py — Window finding, snapping, and cursor-based drag correction.

Windows only. All public functions are no-ops on non-Windows platforms.
"""

import sys
import time

_WINDOWS = sys.platform == "win32"

if _WINDOWS:
    import ctypes
    import ctypes.wintypes
    import math

    _user32 = ctypes.windll.user32

    _MOUSEEVENTF_MOVE      = 0x0001
    _MOUSEEVENTF_LEFTDOWN  = 0x0002
    _MOUSEEVENTF_LEFTUP    = 0x0004
    _MOUSEEVENTF_ABSOLUTE  = 0x8000

    _MONITORS: list = []

    def _detect_monitors():
        rects = []
        MONITORENUMPROC = ctypes.WINFUNCTYPE(
            ctypes.c_int,
            ctypes.wintypes.HMONITOR,
            ctypes.wintypes.HDC,
            ctypes.POINTER(ctypes.wintypes.RECT),
            ctypes.wintypes.LPARAM,
        )
        def _cb(hMon, hdcMon, lpRect, _data):
            r = lpRect.contents
            rects.append({"left": r.left, "top": r.top,
                           "w": r.right - r.left, "h": r.bottom - r.top})
            return 1
        _user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(_cb), 0)
        rects.sort(key=lambda m: (0 if (m["left"] <= 0 < m["left"] + m["w"] and
                                         m["top"]  <= 0 < m["top"]  + m["h"]) else 1,
                                   m["left"], m["top"]))
        return rects

    _MONITORS = _detect_monitors()

    def get_monitor(index):
        if index < len(_MONITORS):
            return _MONITORS[index]
        return _MONITORS[0] if _MONITORS else None

    def find_window(title_substr, timeout=6.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            found = []
            EnumWindowsProc = ctypes.WINFUNCTYPE(
                ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM
            )
            def _cb(hwnd, _):
                if not _user32.IsWindowVisible(hwnd):
                    return True
                length = _user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    _user32.GetWindowTextW(hwnd, buf, length + 1)
                    if title_substr.lower() in buf.value.lower():
                        found.append(hwnd)
                return True
            _user32.EnumWindows(EnumWindowsProc(_cb), 0)
            if found:
                return found[0]
            time.sleep(0.3)
        return None

    _POSITIONS = {
        "left":         (0.0,  0.0,  0.5,  1.0),
        "right":        (0.5,  0.0,  0.5,  1.0),
        "full":         (0.0,  0.0,  1.0,  1.0),
        "left-2/3":     (0.0,  0.0,  2/3,  1.0),
        "right-1/3":    (2/3,  0.0,  1/3,  1.0),
        "left-1/3":     (0.0,  0.0,  1/3,  1.0),
        "right-2/3":    (1/3,  0.0,  2/3,  1.0),
        "top-left":     (0.0,  0.0,  0.5,  0.5),
        "top-right":    (0.5,  0.0,  0.5,  0.5),
        "bottom-left":  (0.0,  0.5,  0.5,  0.5),
        "bottom-right": (0.5,  0.5,  0.5,  0.5),
    }

    _TOLERANCE   = 30
    _SW_RESTORE  = 9
    _SW_MAXIMIZE = 3
    _SWP_NOACTIVATE = 0x0010
    _SWP_SHOWWINDOW = 0x0040

    def _target_rect(position, monitor_index):
        mon = get_monitor(monitor_index)
        if not mon:
            return None
        frac = _POSITIONS.get(position)
        if not frac:
            return None
        xf, yf, wf, hf = frac
        x = mon["left"] + int(mon["w"] * xf)
        y = mon["top"]  + int(mon["h"] * yf)
        w = int(mon["w"] * wf)
        h = int(mon["h"] * hf)
        return x, y, w, h

    def _get_rect(hwnd):
        r = ctypes.wintypes.RECT()
        _user32.GetWindowRect(hwnd, ctypes.byref(r))
        return r.left, r.top, r.right, r.bottom

    def _is_correct(hwnd, tx, ty, tw, th):
        left, top, right, bottom = _get_rect(hwnd)
        return (abs(left - tx) < _TOLERANCE and
                abs(top  - ty) < _TOLERANCE and
                abs((right - left) - tw) < _TOLERANCE)

    def _set_pos(hwnd, x, y, w, h):
        HWND_TOP = ctypes.wintypes.HWND(0)
        _user32.ShowWindow(hwnd, _SW_RESTORE)
        time.sleep(0.1)
        _user32.SetWindowPos(hwnd, HWND_TOP, x, y, w, h, _SWP_SHOWWINDOW)

    def _drag_to(hwnd, tx, ty, tw, th):
        _user32.ShowWindow(hwnd, _SW_RESTORE)
        time.sleep(0.2)
        left, top, right, bottom = _get_rect(hwnd)
        from_x = (left + right) // 2
        from_y  = top + 15
        to_x = tx + tw // 4
        to_y = ty + 15
        _user32.SetForegroundWindow(hwnd)
        time.sleep(0.1)
        _user32.SetCursorPos(from_x, from_y)
        time.sleep(0.1)
        _user32.mouse_event(_MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.05)
        steps = 25
        for i in range(1, steps + 1):
            t  = i / steps
            cx = int(from_x + (to_x - from_x) * t)
            cy = int(from_y + (to_y - from_y) * t)
            _user32.SetCursorPos(cx, cy)
            time.sleep(0.012)
        _user32.mouse_event(_MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        time.sleep(0.3)
        HWND_TOP = ctypes.wintypes.HWND(0)
        _user32.SetWindowPos(hwnd, HWND_TOP, tx, ty, tw, th, _SWP_SHOWWINDOW)
        time.sleep(0.15)
        _user32.ShowWindow(hwnd, _SW_RESTORE)
        _user32.SetWindowPos(hwnd, HWND_TOP, tx, ty, tw, th, _SWP_SHOWWINDOW)

    def snap_and_verify(position, monitor_index=0, hwnd=None,
                        title_substr=None, max_attempts=3):
        if hwnd is None:
            hwnd = find_window(title_substr or "", timeout=1.0)
        if not hwnd:
            return False
        if position == "max":
            mon = get_monitor(monitor_index)
            _user32.SetWindowPos(hwnd, None,
                                 mon["left"] + 50, mon["top"] + 50,
                                 200, 200, _SWP_NOACTIVATE)
            time.sleep(0.05)
            _user32.ShowWindow(hwnd, _SW_MAXIMIZE)
            return True
        target = _target_rect(position, monitor_index)
        if not target:
            return False
        tx, ty, tw, th = target
        for _ in range(max_attempts):
            _set_pos(hwnd, tx, ty, tw, th)
            time.sleep(0.4)
            if _is_correct(hwnd, tx, ty, tw, th):
                return True
            _drag_to(hwnd, tx, ty, tw, th)
            time.sleep(0.4)
            if _is_correct(hwnd, tx, ty, tw, th):
                return True
        return False

else:
    # Non-Windows — window management not available
    def find_window(title_substr, timeout=6.0):
        return None

    def snap_and_verify(position, monitor_index=0, hwnd=None,
                        title_substr=None, max_attempts=3):
        return False

    def get_monitor(index):
        return None
