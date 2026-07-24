"""Display the Windows input mode beside the real text caret."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import sys
import threading
import tkinter as tk

import comtypes
import comtypes.client
from comtypes.gen import UIAutomationClient as UIA
from PIL import Image, ImageDraw, ImageFont
import pystray


POLL_INTERVAL_MS = 50
CARET_OFFSET_X = 6
CARET_OFFSET_Y = 3

GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
HWND_TOPMOST = -1
SW_HIDE = 0
SW_SHOWNOACTIVATE = 4
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
IME_CMODE_NATIVE = 0x0001
OBJID_CARET = -8
S_OK = 0


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class GUITHREADINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hwndActive", wintypes.HWND),
        ("hwndFocus", wintypes.HWND),
        ("hwndCapture", wintypes.HWND),
        ("hwndMenuOwner", wintypes.HWND),
        ("hwndMoveSize", wintypes.HWND),
        ("hwndCaret", wintypes.HWND),
        ("rcCaret", RECT),
    ]


class VARIANT_VALUE(ctypes.Union):
    _fields_ = [
        ("lVal", wintypes.LONG),
        ("ptr", ctypes.c_void_p),
    ]


class VARIANT(ctypes.Structure):
    _anonymous_ = ("value",)
    _fields_ = [
        ("vt", wintypes.USHORT),
        ("wReserved1", wintypes.USHORT),
        ("wReserved2", wintypes.USHORT),
        ("wReserved3", wintypes.USHORT),
        ("value", VARIANT_VALUE),
    ]


user32 = ctypes.WinDLL("user32", use_last_error=True) if sys.platform == "win32" else None
imm32 = ctypes.WinDLL("imm32", use_last_error=True) if sys.platform == "win32" else None
oleacc = ctypes.OleDLL("oleacc", use_last_error=True) if sys.platform == "win32" else None
ole32 = ctypes.OleDLL("ole32", use_last_error=True) if sys.platform == "win32" else None

if user32 is not None:
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetGUIThreadInfo.argtypes = [wintypes.DWORD, ctypes.POINTER(GUITHREADINFO)]
    user32.GetGUIThreadInfo.restype = wintypes.BOOL
    user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
    user32.ClientToScreen.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.c_void_p]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
    user32.GetKeyboardLayout.restype = ctypes.c_void_p
    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongW.restype = wintypes.LONG
    user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]
    user32.SetWindowLongW.restype = wintypes.LONG
    user32.SetWindowPos.argtypes = [
        wintypes.HWND,
        wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    ]
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL

if imm32 is not None:
    imm32.ImmGetContext.argtypes = [wintypes.HWND]
    imm32.ImmGetContext.restype = wintypes.HANDLE
    imm32.ImmGetConversionStatus.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
    ]
    imm32.ImmGetConversionStatus.restype = wintypes.BOOL
    imm32.ImmReleaseContext.argtypes = [wintypes.HWND, wintypes.HANDLE]
    imm32.ImmReleaseContext.restype = wintypes.BOOL

if oleacc is not None:
    oleacc.AccessibleObjectFromWindow.argtypes = [
        wintypes.HWND,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_byte),
        ctypes.POINTER(ctypes.c_void_p),
    ]
    oleacc.AccessibleObjectFromWindow.restype = ctypes.HRESULT


IID_IACCESSIBLE = (ctypes.c_byte * 16)(
    0xE0 - 256, 0x36, 0x87 - 256, 0x61, 0x3D, 0x3C, 0xCF - 256, 0x11,
    0x81 - 256, 0x0C, 0x00, 0xAA - 256, 0x00, 0x38, 0x9B - 256, 0x71,
)


class UIAutomationCaret:
    """Read the caret rectangle exposed by the modern UI Automation API."""

    def __init__(self) -> None:
        self.automation = comtypes.client.CreateObject(
            UIA.CUIAutomation, interface=UIA.IUIAutomation
        )

    def position(self) -> tuple[int, int] | None:
        try:
            focused = self.automation.GetFocusedElement()
            if focused is None:
                return None
            unknown = focused.GetCurrentPattern(UIA.UIA_TextPattern2Id)
            if unknown is None:
                return None
            pattern = unknown.QueryInterface(UIA.IUIAutomationTextPattern2)
            is_active, caret_range = pattern.GetCaretRange()
            if not is_active or caret_range is None:
                return None
            rectangles = caret_range.GetBoundingRectangles()
            if not rectangles or len(rectangles) < 4:
                return None
            left, top, width, height = rectangles[:4]
            return round(left + max(width, 1)), round(top + max(height, 1))
        except (OSError, COMError, ValueError, TypeError):
            return None


COMError = comtypes.COMError
uia_caret: UIAutomationCaret | None = None


def language_label(language_id: int, native_mode: bool | None = None) -> str:
    """Return a compact label, including Korean IME's Hangul/English mode."""
    primary_language = language_id & 0x03FF
    if primary_language == 0x12:
        return "EN" if native_mode is False else "한"
    labels = {
        0x09: "EN",
        0x11: "日",
        0x04: "中",
    }
    return labels.get(primary_language, f"{language_id:04X}")


def korean_native_mode(window: int) -> bool | None:
    """Read the Korean IME conversion mode for the focused control."""
    if imm32 is None or not window:
        return None
    context = imm32.ImmGetContext(window)
    if not context:
        return None
    try:
        conversion = wintypes.DWORD()
        sentence = wintypes.DWORD()
        if not imm32.ImmGetConversionStatus(
            context, ctypes.byref(conversion), ctypes.byref(sentence)
        ):
            return None
        return bool(conversion.value & IME_CMODE_NATIVE)
    finally:
        imm32.ImmReleaseContext(window, context)


def accessible_caret_position(window: int) -> tuple[int, int] | None:
    """Use Microsoft Active Accessibility when a modern app hides its caret."""
    if oleacc is None or not window:
        return None

    accessible = ctypes.c_void_p()
    result = oleacc.AccessibleObjectFromWindow(
        window,
        ctypes.c_ulong(OBJID_CARET & 0xFFFFFFFF),
        IID_IACCESSIBLE,
        ctypes.byref(accessible),
    )
    if result != S_OK or not accessible.value:
        return None

    vtable = ctypes.cast(
        accessible, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))
    ).contents
    release = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtable[2])
    acc_location = ctypes.WINFUNCTYPE(
        ctypes.HRESULT,
        ctypes.c_void_p,
        ctypes.POINTER(wintypes.LONG),
        ctypes.POINTER(wintypes.LONG),
        ctypes.POINTER(wintypes.LONG),
        ctypes.POINTER(wintypes.LONG),
        VARIANT,
    )(vtable[22])
    try:
        left = wintypes.LONG()
        top = wintypes.LONG()
        width = wintypes.LONG()
        height = wintypes.LONG()
        child_self = VARIANT()
        child_self.vt = 3  # VT_I4
        child_self.lVal = 0  # CHILDID_SELF
        result = acc_location(
            accessible,
            ctypes.byref(left),
            ctypes.byref(top),
            ctypes.byref(width),
            ctypes.byref(height),
            child_self,
        )
        if result != S_OK:
            return None
        return left.value + max(width.value, 1), top.value + max(height.value, 1)
    finally:
        release(accessible)


def foreground_input_info() -> tuple[int, GUITHREADINFO, str] | None:
    """Return focused-window information and its current input-mode label."""
    if user32 is None:
        return None

    foreground = user32.GetForegroundWindow()
    if not foreground:
        return None
    thread_id = user32.GetWindowThreadProcessId(foreground, None)

    info = GUITHREADINFO()
    info.cbSize = ctypes.sizeof(GUITHREADINFO)
    if not user32.GetGUIThreadInfo(thread_id, ctypes.byref(info)):
        return None

    keyboard_layout = user32.GetKeyboardLayout(thread_id)
    language_id = int(keyboard_layout or 0) & 0xFFFF
    native_mode = korean_native_mode(info.hwndFocus)
    return foreground, info, language_label(language_id, native_mode)


def caret_and_language() -> tuple[int, int, str] | None:
    """Return caret position via Win32, with an accessibility fallback."""
    state = foreground_input_info()
    if state is None:
        return None
    foreground, info, label = state

    if info.hwndCaret:
        point = wintypes.POINT(info.rcCaret.right, info.rcCaret.bottom)
        if user32.ClientToScreen(info.hwndCaret, ctypes.byref(point)):
            return point.x, point.y, label

    position = uia_caret.position() if uia_caret is not None else None
    if position is None:
        position = accessible_caret_position(info.hwndFocus or foreground)
    if position is None and info.hwndFocus != foreground:
        position = accessible_caret_position(foreground)
    if position is None:
        return None
    return position[0], position[1], label


def tray_image(text: str) -> Image.Image:
    """Create a crisp input-mode system-tray icon."""
    image = Image.new("RGBA", (64, 64), (31, 41, 55, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2, 2, 61, 61), radius=13, fill=(37, 99, 235, 255))
    font_path = r"C:\Windows\Fonts\malgunbd.ttf"
    try:
        font = ImageFont.truetype(font_path, 34 if len(text) == 1 else 25)
    except OSError:
        font = ImageFont.load_default()
    box = draw.textbbox((0, 0), text, font=font)
    x = (64 - (box[2] - box[0])) / 2 - box[0]
    y = (64 - (box[3] - box[1])) / 2 - box[1] - 1
    draw.text((x, y), text, font=font, fill="white")
    return image


class InputLanguageIndicator:
    def __init__(self) -> None:
        global uia_caret
        if ole32 is not None:
            ole32.CoInitialize(None)
        try:
            uia_caret = UIAutomationCaret()
        except (OSError, COMError):
            uia_caret = None
        self.root = tk.Tk()
        self.root.withdraw()
        self.stop_requested = threading.Event()

        self.window = tk.Toplevel(self.root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-alpha", 0.88)

        self.label = tk.Label(
            self.window,
            text="",
            font=("Malgun Gothic", 9, "bold"),
            foreground="#ffffff",
            background="#202124",
            padx=4,
            pady=1,
        )
        self.label.pack()
        self.window.update_idletasks()
        self.hwnd = self.window.winfo_id()

        style = user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
        style |= WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TRANSPARENT
        user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, style)
        self._visible = False
        self._input_label = "EN"

        self.tray = pystray.Icon(
            "InputLanguageIndicator",
            tray_image(self._input_label),
            "입력 언어 표시기 - EN",
            menu=pystray.Menu(
                pystray.MenuItem("입력 언어 표시기", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("종료", self.request_stop),
            ),
        )
        self.tray.run_detached()

    def request_stop(self, _icon=None, _item=None) -> None:
        self.stop_requested.set()

    def set_input_label(self, text: str) -> None:
        if text == self._input_label:
            return
        self._input_label = text
        self.tray.icon = tray_image(text)
        self.tray.title = f"입력 언어 표시기 - {text}"

    def hide(self) -> None:
        if self._visible:
            user32.ShowWindow(self.hwnd, SW_HIDE)
            self._visible = False

    def update(self) -> None:
        if self.stop_requested.is_set():
            self.hide()
            self.tray.stop()
            self.root.destroy()
            return

        state = caret_and_language()
        if state is None:
            self.hide()
            input_info = foreground_input_info()
            if input_info is not None:
                self.set_input_label(input_info[2])
        else:
            x, y, text = state
            self.set_input_label(text)
            if self.label.cget("text") != text:
                self.label.config(text=text)
                self.window.update_idletasks()

            width = self.window.winfo_reqwidth()
            height = self.window.winfo_reqheight()
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            x = min(max(0, x + CARET_OFFSET_X), screen_width - width)
            y = min(max(0, y + CARET_OFFSET_Y), screen_height - height)

            # Move and show without ever activating this window. This keeps the
            # foreground application's caret as the sole tracking target.
            user32.SetWindowPos(
                self.hwnd,
                HWND_TOPMOST,
                x,
                y,
                width,
                height,
                SWP_NOACTIVATE | SWP_SHOWWINDOW,
            )
            if not self._visible:
                user32.ShowWindow(self.hwnd, SW_SHOWNOACTIVATE)
                self._visible = True

        self.root.after(POLL_INTERVAL_MS, self.update)

    def run(self) -> None:
        self.root.after(0, self.update)
        try:
            self.root.mainloop()
        finally:
            self.tray.stop()
            if ole32 is not None:
                ole32.CoUninitialize()


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("이 프로그램은 Windows에서만 실행할 수 있습니다.")
    InputLanguageIndicator().run()


if __name__ == "__main__":
    main()
