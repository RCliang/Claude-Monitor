"""Write text input to a running process's console on Windows."""

import ctypes
import sys
from ctypes import wintypes
from typing import Optional

if sys.platform != "win32":
    raise RuntimeError("console_writer only supports Windows")

kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32

# Console constants
ATTACH_PARENT_PROCESS = -1
STD_INPUT_HANDLE = -10

# Input event types
KEY_EVENT = 0x0001

# Virtual key codes
VK_RETURN = 0x0D
VK_BACK = 0x08


class COORD(ctypes.Structure):
    _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]


class KEY_EVENT_RECORD(ctypes.Structure):
    _fields_ = [
        ("bKeyDown", wintypes.BOOL),
        ("wRepeatCount", wintypes.WORD),
        ("wVirtualKeyCode", wintypes.WORD),
        ("wVirtualScanCode", wintypes.WORD),
        ("uChar", ctypes.c_wchar),
        ("dwControlKeyState", wintypes.DWORD),
    ]


class INPUT_RECORD_UNION(ctypes.Union):
    _fields_ = [("KeyEvent", KEY_EVENT_RECORD)]


class INPUT_RECORD(ctypes.Structure):
    _fields_ = [("EventType", wintypes.WORD), ("Event", INPUT_RECORD_UNION)]


def _make_key_event(char: str, key_down: bool) -> INPUT_RECORD:
    """Create a single key event INPUT_RECORD for a character."""
    record = INPUT_RECORD()
    record.EventType = KEY_EVENT
    event = record.Event.KeyEvent
    event.bKeyDown = key_down
    event.wRepeatCount = 1
    event.dwControlKeyState = 0

    vk = user32.VkKeyScanW(ctypes.c_wchar(char))
    if vk == -1:
        # Character not mappable, use Unicode
        event.wVirtualKeyCode = 0
        event.wVirtualScanCode = 0
        event.uChar = char
    else:
        event.wVirtualKeyCode = vk & 0xFF
        event.wVirtualScanCode = user32.MapVirtualKeyW(vk & 0xFF, 0)
        event.uChar = char

    return record


def _make_enter_event(key_down: bool) -> INPUT_RECORD:
    """Create a single Enter key event."""
    record = INPUT_RECORD()
    record.EventType = KEY_EVENT
    event = record.Event.KeyEvent
    event.bKeyDown = key_down
    event.wRepeatCount = 1
    event.wVirtualKeyCode = VK_RETURN
    event.wVirtualScanCode = user32.MapVirtualKeyW(VK_RETURN, 0)
    event.uChar = "\r"
    event.dwControlKeyState = 0
    return record


def send_text_to_process(pid: int, text: str) -> tuple[bool, Optional[str]]:
    """Send text to a process's console input buffer.

    Args:
        pid: Target process ID.
        text: Text to type into the console.

    Returns:
        (success, error_message)
    """
    if not text or len(text) > 2000:
        return False, "Text is empty or exceeds 2000 characters"

    # Build input records: key_down + key_up for each char, then Enter
    records: list[INPUT_RECORD] = []
    for ch in text:
        records.append(_make_key_event(ch, True))
        records.append(_make_key_event(ch, False))
    records.append(_make_enter_event(True))
    records.append(_make_enter_event(False))

    # Detach from current console (if any)
    kernel32.FreeConsole()

    # Attach to target process's console
    if not kernel32.AttachConsole(pid):
        err = ctypes.get_last_error()
        if err == 5:
            return False, "Access denied — run monitor as Administrator"
        elif err == 87:
            return False, "Invalid PID or process has no console"
        else:
            return False, f"AttachConsole failed with error {err}"

    try:
        handle = kernel32.GetStdHandle(STD_INPUT_HANDLE)
        if not handle or handle == -1:
            return False, "Failed to get console input handle"

        written = wintypes.DWORD()
        arr_type = INPUT_RECORD * len(records)
        input_arr = arr_type(*records)

        result = kernel32.WriteConsoleInputW(
            handle,
            input_arr,
            len(records),
            ctypes.byref(written),
        )

        if not result:
            err = ctypes.get_last_error()
            return False, f"WriteConsoleInput failed with error {err}"

        return True, None

    finally:
        kernel32.FreeConsole()
