"""User-facing actions shared by hotkeys, tray commands, and GUI buttons."""

import os
import time
import webbrowser
from urllib.parse import quote_plus

import keyboard
import pyperclip

from .config import COPY_DELAY_SECONDS
from .constants import (
    NAVIGATION_VK,
    NUMPAD_SCAN_CODE,
    VK_LSHIFT,
    VK_OEM_3,
    VK_RCONTROL,
    VK_RSHIFT,
)
from .native import key_down, key_is_down, key_up, press_extended_vk, press_scan_code, press_vk_key


# 현재 보조키 상태 그대로 `~ 물리 키를 누릅니다.
def press_backtick_key():
    press_vk_key(VK_OEM_3)


# Shift가 눌려 있어도 ` 문자가 들어가도록 Shift를 잠시 해제합니다.
def press_unshifted_backtick_key():
    left_shift_down = key_is_down(VK_LSHIFT)
    right_shift_down = key_is_down(VK_RSHIFT)

    if left_shift_down:
        key_up(VK_LSHIFT)
    if right_shift_down:
        key_up(VK_RSHIFT)

    press_vk_key(VK_OEM_3)

    if left_shift_down:
        key_down(VK_LSHIFT)
    if right_shift_down:
        key_down(VK_RSHIFT)


# CapsLock 숫자 레이어에서 실제 numpad 입력을 보냅니다.
def press_numpad_digit(value):
    press_scan_code(NUMPAD_SCAN_CODE[value])


# 현재 선택된 텍스트를 클립보드로 복사해서 문자열로 가져옵니다.
def copy_selection():
    keyboard.send("ctrl+c")
    time.sleep(COPY_DELAY_SECONDS)
    return pyperclip.paste().strip()


# 선택 텍스트를 Google 검색으로 엽니다.
def search_selected_text():
    text = copy_selection()
    if text:
        webbrowser.open(f"https://www.google.com/search?q={quote_plus(text)}")


# 선택 텍스트를 Google 번역으로 엽니다.
def translate_selected_text():
    text = copy_selection()
    if text:
        url_text = quote_plus(text)
        webbrowser.open(
            f"https://translate.google.co.kr/?hl=ko&sl=auto&tl=ko&text={url_text}&op=translate"
        )


# 외부 브라우저로 URL을 엽니다.
def open_url(url):
    webbrowser.open(url)


# 방향키/Home/End/PageUp/PageDown을 Windows 확장 키 입력으로 보냅니다.
def send_navigation_key(key_name):
    press_extended_vk(NAVIGATION_VK[key_name])


# 오른쪽 Ctrl을 레이어 키로만 사용하고 대상 프로그램에는 순수 이동키를 보냅니다.
def send_right_ctrl_navigation_key(key_name):
    right_ctrl_down = key_is_down(VK_RCONTROL)
    if right_ctrl_down:
        key_up(VK_RCONTROL)

    try:
        send_navigation_key(key_name)
    finally:
        if right_ctrl_down:
            key_down(VK_RCONTROL)


# 프로세스를 즉시 종료합니다.
def force_exit():
    os._exit(0)
