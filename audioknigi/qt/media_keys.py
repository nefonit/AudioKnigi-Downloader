from __future__ import annotations

import ctypes
import os
import time
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, QTimer

from ..logging_utils import app_logger

WM_HOTKEY = 0x0312
WM_APPCOMMAND = 0x0319
APPCOMMAND_MEDIA_NEXTTRACK = 11
APPCOMMAND_MEDIA_PREVIOUSTRACK = 12
APPCOMMAND_MEDIA_PLAY_PAUSE = 14

VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3
MOD_NOREPEAT = 0x4000

_HOTKEY_NEXT = 0xA531
_HOTKEY_PREV = 0xA532
_HOTKEY_PLAY_PAUSE = 0xA533


def _configure_user32(user32):
    """Declare WinAPI pointer-sized signatures before passing an HWND on x64."""
    user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
    user32.RegisterHotKey.restype = wintypes.BOOL
    user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.UnregisterHotKey.restype = wintypes.BOOL
    return user32


class WindowsMediaKeyFilter(QAbstractNativeEventFilter):
    """Route Windows multimedia keys to the audiobook player.

    ``WM_APPCOMMAND`` covers the normal case while the AudioKnigi window owns
    the foreground message queue.  Optional ``RegisterHotKey`` registrations
    make the three media keys work while the window is minimized/in the tray or
    another application is focused.  Registration is enabled only after an
    audiobook has actually been loaded, so AudioKnigi does not steal global
    media keys while its player is unused.
    """

    def __init__(self, window):
        super().__init__()
        self.window = window
        self._registered: set[int] = set()
        self._hwnd = 0
        self._last_dispatch_name = ""
        self._last_dispatch_source = ""
        self._last_dispatch_at = 0.0

    @staticmethod
    def _callback_name_for_app_command(command: int) -> str | None:
        return {
            APPCOMMAND_MEDIA_PLAY_PAUSE: "media_play_pause",
            APPCOMMAND_MEDIA_NEXTTRACK: "media_next_track",
            APPCOMMAND_MEDIA_PREVIOUSTRACK: "media_previous_track",
        }.get(int(command))

    @staticmethod
    def _callback_name_for_hotkey(hotkey_id: int) -> str | None:
        return {
            _HOTKEY_PLAY_PAUSE: "media_play_pause",
            _HOTKEY_NEXT: "media_next_track",
            _HOTKEY_PREV: "media_previous_track",
        }.get(int(hotkey_id))

    def _dispatch(self, callback_name: str | None, source: str = "") -> bool:
        if not callback_name:
            return False
        callback = getattr(self.window, callback_name, None)
        if not callable(callback):
            return False
        # Windows can deliver the same physical media-key press as both a
        # registered WM_HOTKEY and WM_APPCOMMAND. Suppress only the immediate
        # duplicate so Play/Pause cannot toggle twice and end where it started.
        now = time.monotonic()
        if (
            callback_name == self._last_dispatch_name
            and source != self._last_dispatch_source
            and now - self._last_dispatch_at < 0.18
        ):
            return True
        self._last_dispatch_name = callback_name
        self._last_dispatch_source = str(source or "")
        self._last_dispatch_at = now
        QTimer.singleShot(0, callback)
        return True

    def set_global_enabled(self, enabled: bool) -> bool:
        """Enable/disable background media-key handling on Windows.

        Failure to register one or more keys is non-fatal because another media
        application may already own them.  ``WM_APPCOMMAND`` remains available
        whenever Windows delivers it to our own window.
        """
        if os.name != "nt":
            return False
        if not enabled:
            self.unregister_global_hotkeys()
            return False
        try:
            raw_hwnd = int(self.window.winId())
            pointer_value = ctypes.c_void_p(raw_hwnd).value
            if pointer_value is None:
                raise ValueError("Invalid window handle")
            new_hwnd = int(pointer_value)
            if self._registered and self._hwnd == new_hwnd:
                return True
            if self._registered and self._hwnd != new_hwnd:
                # Window recreation (flags/tray transitions) invalidates the
                # HWND used by RegisterHotKey. Unregister from the old handle
                # before registering against the new native window.
                self.unregister_global_hotkeys()
            hwnd = wintypes.HWND(pointer_value)
            user32 = _configure_user32(ctypes.windll.user32)
        except Exception:
            app_logger.debug("Windows media-key registration is unavailable", exc_info=True)
            return False

        registrations = (
            (_HOTKEY_PLAY_PAUSE, VK_MEDIA_PLAY_PAUSE),
            (_HOTKEY_NEXT, VK_MEDIA_NEXT_TRACK),
            (_HOTKEY_PREV, VK_MEDIA_PREV_TRACK),
        )
        self._hwnd = int(pointer_value)
        for hotkey_id, virtual_key in registrations:
            try:
                ok = bool(user32.RegisterHotKey(hwnd, hotkey_id, MOD_NOREPEAT, virtual_key))
                if not ok:
                    # Some Windows/RDP stacks reject MOD_NOREPEAT even though the
                    # media key itself can be registered. De-duplication is also
                    # performed in _dispatch(), so a modifier-free fallback is safe.
                    ok = bool(user32.RegisterHotKey(hwnd, hotkey_id, 0, virtual_key))
            except Exception:
                ok = False
            if ok:
                self._registered.add(hotkey_id)
            else:
                app_logger.info(
                    "MEDIA KEYS | global registration unavailable | id=%s | vk=%s",
                    hotkey_id,
                    virtual_key,
                )
        return bool(self._registered)

    def unregister_global_hotkeys(self) -> None:
        if os.name != "nt" or not self._registered:
            self._registered.clear()
            return
        if not self._hwnd:
            self._registered.clear()
            return
        try:
            user32 = _configure_user32(ctypes.windll.user32)
        except Exception:
            self._registered.clear()
            return
        pointer_value = ctypes.c_void_p(self._hwnd or 0).value
        hwnd = wintypes.HWND(pointer_value)
        for hotkey_id in tuple(self._registered):
            try:
                user32.UnregisterHotKey(hwnd, hotkey_id)
            except Exception:
                pass
        self._registered.clear()
        self._hwnd = 0

    def shutdown(self) -> None:
        self.unregister_global_hotkeys()

    def nativeEventFilter(self, event_type, message):
        if os.name != "nt":
            return False, 0
        try:
            address = int(message)
            if not address:
                return False, 0
            msg = wintypes.MSG.from_address(address)
        except Exception:
            return False, 0

        if int(msg.message) == WM_HOTKEY:
            callback_name = self._callback_name_for_hotkey(int(msg.wParam))
            if callback_name and self._dispatch(callback_name, "hotkey"):
                return True, 0
            return False, 0

        if int(msg.message) != WM_APPCOMMAND:
            return False, 0
        # GET_APPCOMMAND_LPARAM: high word with the device bits removed.
        command = (int(msg.lParam) >> 16) & 0x0FFF
        callback_name = self._callback_name_for_app_command(command)
        if callback_name and self._dispatch(callback_name, "appcommand"):
            return True, 0
        return False, 0


__all__ = [
    "WindowsMediaKeyFilter", "WM_HOTKEY", "WM_APPCOMMAND",
    "APPCOMMAND_MEDIA_NEXTTRACK", "APPCOMMAND_MEDIA_PREVIOUSTRACK",
    "APPCOMMAND_MEDIA_PLAY_PAUSE", "VK_MEDIA_NEXT_TRACK",
    "VK_MEDIA_PREV_TRACK", "VK_MEDIA_PLAY_PAUSE",
]
