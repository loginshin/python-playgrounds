"""LoGinKeyboard macOS variant.

This implementation is intentionally separate from the Windows version.
It uses a Quartz event tap so handled layer keys can be suppressed while
normal keyboard input continues to pass through.

Important macOS setup:
    Remap Caps Lock to F18 with Karabiner-Elements, then use F18 as the
    LoGinKeyboard layer key. Native Caps Lock does not provide reliable
    press/release events for this use case on macOS.
"""

from __future__ import annotations

import os
import platform
import threading
import time
import tkinter as tk
import webbrowser
from dataclasses import dataclass
from urllib.parse import quote_plus

import pyperclip

if platform.system() != "Darwin":
    raise SystemExit("LoGinKeyboard macOS version must be run on macOS.")

try:
    import Quartz
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: pyobjc-framework-Quartz. "
        "Install with: python3 -m pip install -r macos/requirements-macos.txt"
    ) from exc


APP_VERSION = "3.1.4-macos"
APP_TITLE = f"LoGinKeyboard {APP_VERSION}"
BLOG_URL = "https://loginshin.tistory.com/17"
QUESTION_URL = "https://open.kakao.com/o/sVFNtrrf"
COPY_DELAY_SECONDS = 0.08
LAYER_TOGGLE_HOLD_SECONDS = 1.0

# macOS virtual key codes. The layer key expects Caps Lock to be remapped to F18.
KEY_A = 0
KEY_S = 1
KEY_D = 2
KEY_H = 4
KEY_Z = 6
KEY_X = 7
KEY_C = 8
KEY_Q = 12
KEY_W = 13
KEY_E = 14
KEY_I = 34
KEY_J = 38
KEY_K = 40
KEY_L = 37
KEY_BACKTICK = 50
KEY_TAB = 48
KEY_SPACE = 49
KEY_ESCAPE = 53
KEY_LEFT_SHIFT = 56
KEY_LEFT_CONTROL = 59
KEY_RIGHT_SHIFT = 60
KEY_RIGHT_CONTROL = 62
KEY_F18 = 79
KEY_RETURN = 36
KEY_CAPS_LOCK = 57
KEY_LEFT_ARROW = 123
KEY_RIGHT_ARROW = 124
KEY_DOWN_ARROW = 125
KEY_UP_ARROW = 126
KEY_HOME = 115
KEY_PAGE_UP = 116
KEY_FORWARD_DELETE = 117
KEY_END = 119
KEY_PAGE_DOWN = 121

KEYPAD_DIGITS = {
    "0": 82,
    "1": 83,
    "2": 84,
    "3": 85,
    "4": 86,
    "5": 87,
    "6": 88,
    "7": 89,
    "8": 91,
    "9": 92,
}

ARROW_TO_NAVIGATION = {
    KEY_LEFT_ARROW: KEY_HOME,
    KEY_RIGHT_ARROW: KEY_END,
    KEY_UP_ARROW: KEY_PAGE_UP,
    KEY_DOWN_ARROW: KEY_PAGE_DOWN,
}

CAPS_NAVIGATION_LAYER = {
    KEY_I: (KEY_UP_ARROW, KEY_PAGE_UP),
    KEY_J: (KEY_LEFT_ARROW, KEY_HOME),
    KEY_K: (KEY_DOWN_ARROW, KEY_PAGE_DOWN),
    KEY_L: (KEY_RIGHT_ARROW, KEY_END),
}

NUMBER_LAYER = {
    KEY_SPACE: "0",
    KEY_Z: "1",
    KEY_X: "2",
    KEY_C: "3",
    KEY_A: "4",
    KEY_S: "5",
    KEY_D: "6",
    KEY_Q: "7",
    KEY_W: "8",
    KEY_E: "9",
}

EVENT_MASK = (
    Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown)
    | Quartz.CGEventMaskBit(Quartz.kCGEventKeyUp)
    | Quartz.CGEventMaskBit(Quartz.kCGEventFlagsChanged)
)


@dataclass
class ModifierState:
    right_control: bool = False
    left_control: bool = False
    right_shift: bool = False
    left_shift: bool = False

    @property
    def any_control(self) -> bool:
        return self.left_control or self.right_control

    @property
    def any_shift(self) -> bool:
        return self.left_shift or self.right_shift


class MacLoginKeyboard:
    """Quartz event-tap based keyboard layer for macOS."""

    def __init__(self) -> None:
        self.modifiers = ModifierState()
        self.layer_down_at: float | None = None
        self.layer_combo_used = False
        self.h_prefix_down = False
        self.gui_root: tk.Tk | None = None
        self.gui_lock = threading.Lock()
        self.event_tap = None
        self.run_loop_source = None

    # Builds one macOS keyboard event for key press/release.
    def create_key_event(self, key_code: int, is_down: bool, flags: int = 0):
        event = Quartz.CGEventCreateKeyboardEvent(None, key_code, is_down)
        if flags:
            Quartz.CGEventSetFlags(event, flags)
        return event

    # Posts a single key press with optional modifier flags.
    def tap_key(self, key_code: int, flags: int = 0) -> None:
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, self.create_key_event(key_code, True, flags))
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, self.create_key_event(key_code, False, flags))

    # Sends Cmd+C to copy selected text.
    def copy_selection(self) -> str:
        self.tap_key(KEY_C, Quartz.kCGEventFlagMaskCommand)
        time.sleep(COPY_DELAY_SECONDS)
        return pyperclip.paste().strip()

    # Opens Google Search for the selected text.
    def search_selected_text(self) -> None:
        text = self.copy_selection()
        if text:
            webbrowser.open(f"https://www.google.com/search?q={quote_plus(text)}")

    # Opens Google Translate for the selected text.
    def translate_selected_text(self) -> None:
        text = self.copy_selection()
        if text:
            url_text = quote_plus(text)
            webbrowser.open(
                f"https://translate.google.co.kr/?hl=ko&sl=auto&tl=ko&text={url_text}&op=translate"
            )

    # Opens an external URL in the default browser.
    def open_url(self, url: str) -> None:
        webbrowser.open(url)

    # Shows or focuses the help/practice window.
    def show_help_gui(self) -> None:
        def build_gui() -> None:
            with self.gui_lock:
                if self.gui_root is not None and self.gui_root.winfo_exists():
                    self.gui_root.deiconify()
                    self.gui_root.lift()
                    self.gui_root.focus_force()
                    return

                root = tk.Tk()
                self.gui_root = root
                root.title(APP_TITLE)
                root.geometry("920x560")
                root.resizable(False, False)
                root.attributes("-topmost", True)
                root.configure(bg="#101418")

                def close_gui() -> None:
                    root.destroy()
                    self.gui_root = None

                root.protocol("WM_DELETE_WINDOW", close_gui)

                colors = {
                    "bg": "#101418",
                    "panel": "#171d24",
                    "text": "#eef3f8",
                    "muted": "#aeb9c6",
                    "accent": "#53d18d",
                    "line": "#2c3744",
                }

                def label(text: str, x: int, y: int, size: int = 12, color: str = "text") -> None:
                    tk.Label(
                        root,
                        text=text,
                        font=("Helvetica Neue", size),
                        fg=colors[color],
                        bg=colors["bg"],
                        anchor="w",
                        justify="left",
                    ).place(x=x, y=y)

                label("LoGinKeyboard macOS", 36, 28, 24)
                label("Caps Lock must be remapped to F18 before using this app.", 40, 72, 12, "muted")
                label("F18 + I/J/K/L  =>  Arrow keys", 52, 130)
                label("F18 + H + J/L/I/K  =>  Home / End / PageUp / PageDown", 52, 165)
                label("F18 + Space/Z/X/C/A/S/D/Q/W/E  =>  Keypad 0-9", 52, 200)
                label("F18 + Arrow keys  =>  Real arrow keys", 52, 235)
                label("Right Control + Arrow keys  =>  Home / End / PageUp / PageDown", 52, 285)
                label("Right Control + Return  =>  Google search selected text", 52, 320)
                label("Right Control + Right Shift  =>  Translate selected text", 52, 355)
                label("Control + Shift + Q  =>  Quit", 52, 390)
                label("Required permission: System Settings > Privacy & Security > Accessibility", 52, 450, 11, "muted")

                tk.Button(
                    root,
                    text="Close",
                    command=close_gui,
                    fg=colors["text"],
                    bg="#263140",
                    activeforeground=colors["text"],
                    activebackground="#344257",
                    relief="flat",
                    bd=0,
                ).place(x=790, y=480, width=88, height=34)

                root.mainloop()

        threading.Thread(target=build_gui, daemon=True).start()

    # Marks the F18 layer as used by a combination.
    def mark_layer_combo_used(self) -> None:
        self.layer_combo_used = True

    # Returns True while the remapped Caps/F18 layer is held.
    def layer_active(self) -> bool:
        return self.layer_down_at is not None

    # Handles F18 down/up and short/long press behavior.
    def handle_layer_key(self, event_type: int) -> None:
        if event_type == Quartz.kCGEventKeyDown:
            self.layer_down_at = time.monotonic()
            self.layer_combo_used = False
            self.h_prefix_down = False
            if self.modifiers.right_control:
                self.show_help_gui()
                self.mark_layer_combo_used()
            return

        if self.layer_down_at is None:
            return

        held_for = time.monotonic() - self.layer_down_at
        self.layer_down_at = None
        self.h_prefix_down = False

        if self.layer_combo_used:
            return
        if held_for >= LAYER_TOGGLE_HOLD_SECONDS:
            self.tap_key(KEY_CAPS_LOCK)
        else:
            self.tap_key(KEY_SPACE, Quartz.kCGEventFlagMaskControl)

    # Updates tracked right/left modifier state from flagsChanged events.
    def update_modifier_state(self, key_code: int, flags: int) -> None:
        if key_code == KEY_RIGHT_CONTROL:
            self.modifiers.right_control = bool(flags & Quartz.kCGEventFlagMaskControl)
        elif key_code == KEY_LEFT_CONTROL:
            self.modifiers.left_control = bool(flags & Quartz.kCGEventFlagMaskControl)
        elif key_code == KEY_RIGHT_SHIFT:
            self.modifiers.right_shift = bool(flags & Quartz.kCGEventFlagMaskShift)
        elif key_code == KEY_LEFT_SHIFT:
            self.modifiers.left_shift = bool(flags & Quartz.kCGEventFlagMaskShift)

    # Handles key-down events that should be converted into LoGinKeyboard actions.
    def handle_key_down(self, key_code: int) -> bool:
        if self.modifiers.any_control and self.modifiers.any_shift and key_code == KEY_Q:
            os._exit(0)

        if self.modifiers.right_control and key_code == KEY_RETURN:
            self.search_selected_text()
            return True

        if self.modifiers.right_control and key_code in ARROW_TO_NAVIGATION:
            self.tap_key(ARROW_TO_NAVIGATION[key_code])
            return True

        if self.modifiers.right_shift and key_code == KEY_ESCAPE:
            flags = 0 if self.modifiers.left_shift else Quartz.kCGEventFlagMaskShift
            self.tap_key(KEY_BACKTICK, flags)
            return True

        if not self.layer_active():
            return False

        self.mark_layer_combo_used()

        if key_code == KEY_TAB:
            self.tap_key(KEY_CAPS_LOCK)
            return True

        if key_code == KEY_ESCAPE:
            self.tap_key(KEY_BACKTICK)
            return True

        if key_code == KEY_H:
            self.h_prefix_down = True
            return True

        if key_code in CAPS_NAVIGATION_LAYER:
            normal_key, h_prefix_key = CAPS_NAVIGATION_LAYER[key_code]
            self.tap_key(h_prefix_key if self.h_prefix_down else normal_key)
            return True

        if key_code in NUMBER_LAYER:
            self.tap_key(KEYPAD_DIGITS[NUMBER_LAYER[key_code]])
            return True

        if key_code in ARROW_TO_NAVIGATION:
            self.tap_key(key_code)
            return True

        return False

    # Handles key-up events that affect layer-prefix state.
    def handle_key_up(self, key_code: int) -> bool:
        if key_code == KEY_H and self.layer_active():
            self.h_prefix_down = False
            return True
        return self.layer_active() and key_code in CAPS_NAVIGATION_LAYER

    # Main Quartz event tap callback. Return None to suppress handled events.
    def callback(self, _proxy, event_type, event, _refcon):
        key_code = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
        flags = Quartz.CGEventGetFlags(event)

        if event_type == Quartz.kCGEventFlagsChanged:
            self.update_modifier_state(key_code, flags)
            if self.modifiers.right_control and key_code == KEY_RIGHT_SHIFT and self.modifiers.right_shift:
                self.translate_selected_text()
                return None
            return event

        if key_code == KEY_F18:
            self.handle_layer_key(event_type)
            return None

        if event_type == Quartz.kCGEventKeyDown and self.handle_key_down(key_code):
            return None

        if event_type == Quartz.kCGEventKeyUp and self.handle_key_up(key_code):
            return None

        return event

    # Installs the event tap and enters the macOS run loop.
    def run(self) -> None:
        self.show_help_gui()
        self.event_tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionDefault,
            EVENT_MASK,
            self.callback,
            None,
        )
        if not self.event_tap:
            raise SystemExit(
                "Could not create keyboard event tap. "
                "Grant Accessibility permission and restart the app."
            )

        self.run_loop_source = Quartz.CFMachPortCreateRunLoopSource(None, self.event_tap, 0)
        Quartz.CFRunLoopAddSource(
            Quartz.CFRunLoopGetCurrent(),
            self.run_loop_source,
            Quartz.kCFRunLoopCommonModes,
        )
        Quartz.CGEventTapEnable(self.event_tap, True)
        Quartz.CFRunLoopRun()


def main() -> None:
    app = MacLoginKeyboard()
    app.run()


if __name__ == "__main__":
    main()
