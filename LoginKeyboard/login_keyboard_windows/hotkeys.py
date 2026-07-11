"""Global keyboard hotkey and CapsLock-layer registration."""

import time

import keyboard

from .actions import (
    press_backtick_key,
    press_numpad_digit,
    press_unshifted_backtick_key,
    search_selected_text,
    send_navigation_key,
    translate_selected_text,
)
from .config import CAPSLOCK_TOGGLE_HOLD_SECONDS
from .constants import (
    CAPS_ARROW_HOTKEYS,
    CAPS_NAVIGATION_LAYER,
    NUMBER_LAYER,
    RIGHT_CTRL_NAVIGATION,
    VK_CAPITAL,
    VK_HANGUL,
)
from .help_gui import show_help_gui
from .native import press_vk
from .tray import quit_app

caps_down_at = None
caps_combo_used = False
caps_h_prefix_down = False


# 실제 CapsLock 토글 키 입력을 보냅니다.
def toggle_capslock():
    press_vk(VK_CAPITAL)


# CapsLock이 단독 입력이 아니라 조합키로 쓰였음을 기록합니다.
def mark_caps_combo_used():
    global caps_combo_used
    caps_combo_used = True


# CapsLock 누름 시각을 저장해 단독/길게 누름을 구분할 준비를 합니다.
def on_caps_down(_event):
    global caps_down_at, caps_combo_used
    caps_down_at = time.monotonic()
    caps_combo_used = False


# CapsLock을 뗄 때 단독 입력, 길게 누름, 조합 입력을 판정합니다.
def on_caps_up(_event):
    global caps_down_at, caps_combo_used, caps_h_prefix_down
    if caps_down_at is None:
        return

    held_for = time.monotonic() - caps_down_at
    caps_down_at = None
    caps_h_prefix_down = False

    if caps_combo_used:
        return
    if held_for >= CAPSLOCK_TOGGLE_HOLD_SECONDS:
        toggle_capslock()
    else:
        press_vk(VK_HANGUL)


# CapsLock hotkey 콜백을 조합 입력으로 표시한 뒤 실행하게 감쌉니다.
def combo(action):
    def wrapped():
        mark_caps_combo_used()
        action()

    return wrapped


# Right Ctrl + Right Shift 조합으로 번역 기능을 실행합니다.
def handle_translate_shift(event):
    if event.event_type == "down" and keyboard.is_pressed("right ctrl"):
        translate_selected_text()
        return False
    return True


# CapsLock 레이어가 현재 활성 상태인지 확인합니다.
def caps_layer_active():
    return caps_down_at is not None or keyboard.is_pressed("caps lock")


# CapsLock 레이어에서 숫자/특수 동작 키를 처리합니다.
def handle_caps_layer_key(event, action):
    if not caps_layer_active():
        return True

    mark_caps_combo_used()
    if event.event_type == "down":
        action()
    return False


# CapsLock + H prefix 상태를 기록합니다.
def handle_caps_h(event):
    global caps_h_prefix_down
    if not caps_layer_active():
        return True

    mark_caps_combo_used()
    caps_h_prefix_down = event.event_type == "down"
    return False


# CapsLock 방향 레이어에서 일반 이동키와 H prefix 이동키를 분기합니다.
def handle_caps_navigation_key(event, normal_key, h_prefix_key):
    if not caps_layer_active():
        return True

    mark_caps_combo_used()
    if event.event_type == "down":
        send_navigation_key(h_prefix_key if caps_h_prefix_down else normal_key)
    return False


# 환경에 따라 차단 실패가 가능한 키들을 가능한 범위에서만 막습니다.
def block_best_effort(*key_names):
    for key_name in key_names:
        try:
            keyboard.block_key(key_name)
        except Exception:
            pass


# 앱에서 쓰는 모든 전역 hotkey/hook을 등록합니다.
def register_hotkeys():
    block_best_effort("hanja", "hangul", "scroll lock")

    keyboard.add_hotkey("right ctrl+caps lock", show_help_gui, suppress=True)
    for hotkey, target_key in RIGHT_CTRL_NAVIGATION.items():
        keyboard.add_hotkey(hotkey, lambda key=target_key: keyboard.send(key), suppress=True)
    keyboard.add_hotkey("right ctrl+enter", search_selected_text, suppress=True)
    keyboard.hook_key("right shift", handle_translate_shift, suppress=True)

    keyboard.add_hotkey("right shift+left shift+esc", press_unshifted_backtick_key, suppress=True)
    keyboard.add_hotkey("right shift+esc", press_backtick_key, suppress=True)

    keyboard.on_press_key("caps lock", on_caps_down, suppress=True)
    keyboard.on_release_key("caps lock", on_caps_up, suppress=True)
    keyboard.add_hotkey("caps lock+tab", combo(toggle_capslock), suppress=True)

    keyboard.hook_key("h", handle_caps_h, suppress=True)
    for key, (normal_key, h_prefix_key) in CAPS_NAVIGATION_LAYER.items():
        keyboard.hook_key(
            key,
            lambda event, normal=normal_key, prefix=h_prefix_key: handle_caps_navigation_key(
                event,
                normal,
                prefix,
            ),
            suppress=True,
        )

    for key, value in NUMBER_LAYER.items():
        keyboard.hook_key(
            key,
            lambda event, v=value: handle_caps_layer_key(event, lambda: press_numpad_digit(v)),
            suppress=True,
        )

    keyboard.add_hotkey("caps lock+esc", combo(press_unshifted_backtick_key), suppress=True)
    for hotkey, key_name in CAPS_ARROW_HOTKEYS.items():
        keyboard.add_hotkey(hotkey, combo(lambda key=key_name: send_navigation_key(key)), suppress=True)

    keyboard.add_hotkey("ctrl+shift+q", quit_app, suppress=True)

