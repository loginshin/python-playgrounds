"""Low-level Windows API wrappers for keyboard, process, and mouse-hook work."""

import ctypes
import ctypes.wintypes
import os
import sys
import threading
from tkinter import messagebox

from .config import LEAGUE_CLIENT_PROCESS, MUTEX_NAME
from .constants import (
    KEYEVENTF_EXTENDEDKEY,
    KEYEVENTF_KEYUP,
    PROCESS_QUERY_LIMITED_INFORMATION,
    VK_CAPITAL,
    VK_NUMLOCK,
    VK_SCROLL,
    WH_MOUSE_LL,
    WM_LBUTTONDOWN,
)

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
shell32 = ctypes.windll.shell32

mouse_proc_ref = None

INPUT_KEYBOARD = 1
KEYEVENTF_SCANCODE = 0x0008


class KEYBDINPUT(ctypes.Structure):
    _fields_ = (
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_size_t),
    )


class MOUSEINPUT(ctypes.Structure):
    _fields_ = (
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_size_t),
    )


class INPUT_UNION(ctypes.Union):
    _fields_ = (("ki", KEYBDINPUT), ("mi", MOUSEINPUT))


class INPUT(ctypes.Structure):
    _anonymous_ = ("data",)
    _fields_ = (("type", ctypes.c_ulong), ("data", INPUT_UNION))


# Windows 가상키를 한 번 눌렀다 떼는 가장 기본 입력 함수입니다.
def press_vk(vk_code):
    user32.keybd_event(vk_code, 0, 0, 0)
    user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)


# 방향키처럼 확장 키 플래그가 필요한 가상키 입력을 보냅니다.
def press_extended_vk(vk_code):
    user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
    user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)


# 일반 가상키 입력을 명확한 이름으로 감싼 별칭입니다.
def press_vk_key(vk_code):
    user32.keybd_event(vk_code, 0, 0, 0)
    user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)


# 실제 키보드 위치의 스캔 코드를 보내 프로그램이 넘버패드 키로 인식하게 합니다.
def press_scan_code(scan_code):
    inputs = (INPUT * 2)(
        INPUT(
            type=INPUT_KEYBOARD,
            data=INPUT_UNION(
                ki=KEYBDINPUT(wVk=0, wScan=scan_code, dwFlags=KEYEVENTF_SCANCODE)
            ),
        ),
        INPUT(
            type=INPUT_KEYBOARD,
            data=INPUT_UNION(
                ki=KEYBDINPUT(
                    wVk=0,
                    wScan=scan_code,
                    dwFlags=KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP,
                )
            ),
        ),
    )
    sent_count = user32.SendInput(len(inputs), inputs, ctypes.sizeof(INPUT))
    if sent_count != len(inputs):
        raise ctypes.WinError(ctypes.get_last_error())


# 특정 가상키가 현재 눌려 있는지 확인합니다.
def key_is_down(vk_code):
    return bool(user32.GetKeyState(vk_code) & 0x8000)


# Shift 상태를 잠시 해제했다 복구할 때 쓰는 key down 래퍼입니다.
def key_down(vk_code):
    user32.keybd_event(vk_code, 0, 0, 0)


# Shift 상태를 잠시 해제했다 복구할 때 쓰는 key up 래퍼입니다.
def key_up(vk_code):
    user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)


# CapsLock/NumLock/ScrollLock 같은 토글 키의 현재 토글 상태를 읽습니다.
def is_toggled(vk_code):
    return bool(user32.GetKeyState(vk_code) & 1)


# 토글 키가 원하는 상태와 다를 때만 실제 키 입력으로 상태를 바꿉니다.
def set_toggle_state(vk_code, enabled):
    if is_toggled(vk_code) != enabled:
        press_vk(vk_code)


# 앱이 기대하는 Lock 키 기본값을 맞춥니다.
def keep_lock_keys_stable():
    set_toggle_state(VK_NUMLOCK, True)
    set_toggle_state(VK_CAPITAL, False)
    set_toggle_state(VK_SCROLL, False)


# 현재 포그라운드 창을 소유한 프로세스 파일명을 반환합니다.
def foreground_process_name():
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""

    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return ""

    process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not process:
        return ""

    try:
        buffer_size = ctypes.c_ulong(260)
        buffer = ctypes.create_unicode_buffer(buffer_size.value)
        if kernel32.QueryFullProcessImageNameW(process, 0, buffer, ctypes.byref(buffer_size)):
            return os.path.basename(buffer.value)
        return ""
    finally:
        kernel32.CloseHandle(process)


# League Client 클릭 감지를 위한 저수준 마우스 훅을 시작합니다.
def start_league_client_exit_hook():
    def hook_thread():
        global mouse_proc_ref
        low_level_mouse_proc = ctypes.WINFUNCTYPE(
            ctypes.c_long,
            ctypes.c_int,
            ctypes.c_uint,
            ctypes.c_void_p,
        )

        def mouse_proc(n_code, w_param, l_param):
            if n_code >= 0 and w_param == WM_LBUTTONDOWN:
                if foreground_process_name().lower() == LEAGUE_CLIENT_PROCESS:
                    os._exit(0)
            return user32.CallNextHookEx(None, n_code, w_param, l_param)

        mouse_proc_ref = low_level_mouse_proc(mouse_proc)
        hook = user32.SetWindowsHookExW(WH_MOUSE_LL, mouse_proc_ref, kernel32.GetModuleHandleW(None), 0)
        if not hook:
            return

        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    threading.Thread(target=hook_thread, daemon=True).start()


# 전역 Mutex로 앱 중복 실행을 막습니다.
def ensure_single_instance():
    handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if handle and kernel32.GetLastError() == 183:
        messagebox.showinfo("LoGinKeyboard", "LoGinKeyboard가 이미 실행 중입니다.")
        sys.exit(0)
