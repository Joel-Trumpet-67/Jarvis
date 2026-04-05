"""
windows.py — Window finding and snapping via ctypes (no extra deps).

Monitors detected at import time. Snap positions are relative to a
named monitor slot so scenes don't hard-code pixel offsets.
"""

import ctypes
import ctypes.wintypes
import time

_user32 = ctypes.windll.user32

# ── Monitor detection ────────────────────────────────────────────────────────

_MONITORS: list[dict] = []   # [{left, top, w, h}, ...]

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

    # Sort so primary (containing 0,0) is index 0
    rects.sort(key=lambda m: (0 if (m["left"] <= 0 < m["left"] + m["w"] and
                                     m["top"]  <= 0 < m["top"]  + m["h"]) else 1,
                               m["left"], m["top"]))
    return rects

_MONITORS = _detect_monitors()


def get_monitor(index: int) -> dict | None:
    if index < len(_MONITORS):
        return _MONITORS[index]
    return _MONITORS[0] if _MONITORS else None


# ── Window finding ───────────────────────────────────────────────────────────

def find_window(title_substr: str, timeout: float = 6.0) -> int | None:
    """
    Poll until a visible window whose title contains `title_substr` appears,
    or timeout expires. Returns HWND int or None.
    """
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


# ── Window snapping ──────────────────────────────────────────────────────────

_SWP_NOACTIVATE = 0x0010
_SWP_SHOWWINDOW = 0x0040
_SW_RESTORE     = 9
_SW_MAXIMIZE    = 3

_POSITIONS = {
    # position_name: (x_offset_fraction, y_offset_fraction, w_fraction, h_fraction)
    "left":         (0.0,  0.0,  0.5,  1.0),
    "right":        (0.5,  0.0,  0.5,  1.0),
    "full":         (0.0,  0.0,  1.0,  1.0),
    "top-left":     (0.0,  0.0,  0.5,  0.5),
    "top-right":    (0.5,  0.0,  0.5,  0.5),
    "bottom-left":  (0.0,  0.5,  0.5,  0.5),
    "bottom-right": (0.5,  0.5,  0.5,  0.5),
}


def snap(title_substr: str, position: str, monitor_index: int = 0) -> bool:
    """
    Find a window by title and snap it to a named position on a monitor.
    Returns True if successful.
    """
    mon = get_monitor(monitor_index)
    if not mon:
        return False

    hwnd = find_window(title_substr, timeout=0.1)
    if not hwnd:
        return False

    # Restore first (de-maximise / un-minimise)
    _user32.ShowWindow(hwnd, _SW_RESTORE)
    time.sleep(0.05)

    if position == "max":
        _user32.SetForegroundWindow(hwnd)
        _user32.ShowWindow(hwnd, _SW_MAXIMIZE)
        return True

    frac = _POSITIONS.get(position)
    if not frac:
        return False

    xf, yf, wf, hf = frac
    x = mon["left"] + int(mon["w"] * xf)
    y = mon["top"]  + int(mon["h"] * yf)
    w = int(mon["w"] * wf)
    h = int(mon["h"] * hf)

    flags = _SWP_SHOWWINDOW
    _user32.SetWindowPos(hwnd, None, x, y, w, h, flags)
    return True
