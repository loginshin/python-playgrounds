"""Native Windows system tray integration."""

import ctypes
import ctypes.wintypes
import threading

import keyboard

from .actions import force_exit, open_url
from .config import APP_TITLE, BLOG_URL, TRAY_CLASS_NAME
from .constants import (
    IDI_APPLICATION,
    MF_STRING,
    NIF_ICON,
    NIF_MESSAGE,
    NIF_TIP,
    NIM_ADD,
    NIM_DELETE,
    TPM_RIGHTBUTTON,
    TRAY_EXIT,
    TRAY_OPEN_BLOG,
    TRAY_OPEN_HELP,
    TRAY_UID,
    WM_COMMAND,
    WM_DESTROY,
    WM_LBUTTONDBLCLK,
    WM_RBUTTONUP,
    WM_TRAYICON,
)
from .help_gui import show_help_gui
from .native import kernel32, shell32, user32

LRESULT = ctypes.c_longlong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_long
WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT,
    ctypes.wintypes.HWND,
    ctypes.wintypes.UINT,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM,
)


# Windows에 숨은 트레이 메시지 윈도우 클래스를 등록할 때 쓰는 구조체입니다.
class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", ctypes.wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", ctypes.wintypes.HINSTANCE),
        ("hIcon", ctypes.wintypes.HANDLE),
        ("hCursor", ctypes.wintypes.HANDLE),
        ("hbrBackground", ctypes.wintypes.HANDLE),
        ("lpszMenuName", ctypes.wintypes.LPCWSTR),
        ("lpszClassName", ctypes.wintypes.LPCWSTR),
    ]


# Windows Shell 트레이 아이콘 등록/삭제에 넘기는 구조체입니다.
class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.wintypes.DWORD),
        ("hWnd", ctypes.wintypes.HWND),
        ("uID", ctypes.wintypes.UINT),
        ("uFlags", ctypes.wintypes.UINT),
        ("uCallbackMessage", ctypes.wintypes.UINT),
        ("hIcon", ctypes.wintypes.HANDLE),
        ("szTip", ctypes.c_wchar * 128),
        ("dwState", ctypes.wintypes.DWORD),
        ("dwStateMask", ctypes.wintypes.DWORD),
        ("szInfo", ctypes.c_wchar * 256),
        ("uTimeoutOrVersion", ctypes.wintypes.UINT),
        ("szInfoTitle", ctypes.c_wchar * 64),
        ("dwInfoFlags", ctypes.wintypes.DWORD),
        ("guidItem", ctypes.c_byte * 16),
        ("hBalloonIcon", ctypes.wintypes.HANDLE),
    ]


tray_hwnd = None
tray_wndproc_ref = None


# Windows Shell API에 트레이 아이콘을 추가합니다.
def add_native_tray_icon(hwnd):
    data = NOTIFYICONDATAW()
    data.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
    data.hWnd = hwnd
    data.uID = TRAY_UID
    data.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
    data.uCallbackMessage = WM_TRAYICON
    data.hIcon = user32.LoadIconW(None, IDI_APPLICATION)
    data.szTip = APP_TITLE
    shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(data))


# 앱 종료 시 Windows Shell API에서 트레이 아이콘을 제거합니다.
def remove_native_tray_icon():
    if not tray_hwnd:
        return

    data = NOTIFYICONDATAW()
    data.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
    data.hWnd = tray_hwnd
    data.uID = TRAY_UID
    shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(data))


# 모든 키보드 훅과 트레이 아이콘을 정리한 뒤 프로세스를 종료합니다.
def quit_app(_icon=None, _item=None):
    try:
        keyboard.unhook_all()
    except Exception:
        pass

    try:
        remove_native_tray_icon()
    except Exception:
        pass

    force_exit()


# 트레이 아이콘 우클릭 메뉴를 생성하고 현재 커서 위치에 표시합니다.
def show_native_tray_menu(hwnd):
    menu = user32.CreatePopupMenu()
    user32.AppendMenuW(menu, MF_STRING, TRAY_OPEN_HELP, "도움말 열기")
    user32.AppendMenuW(menu, MF_STRING, TRAY_OPEN_BLOG, "블로그 열기")
    user32.AppendMenuW(menu, MF_STRING, TRAY_EXIT, "종료")

    point = ctypes.wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(point))
    user32.SetForegroundWindow(hwnd)
    user32.TrackPopupMenu(menu, TPM_RIGHTBUTTON, point.x, point.y, 0, hwnd, None)
    user32.DestroyMenu(menu)


# 트레이 메뉴 command id를 실제 동작 함수로 분기합니다.
def handle_tray_command(command_id):
    if command_id == TRAY_OPEN_HELP:
        show_help_gui()
    elif command_id == TRAY_OPEN_BLOG:
        open_url(BLOG_URL)
    elif command_id == TRAY_EXIT:
        quit_app()


# 숨은 트레이 윈도우가 받는 Windows 메시지를 처리합니다.
def tray_window_proc(hwnd, msg, w_param, l_param):
    if msg == WM_TRAYICON:
        if l_param == WM_LBUTTONDBLCLK:
            show_help_gui()
        elif l_param == WM_RBUTTONUP:
            show_native_tray_menu(hwnd)
        return 0

    if msg == WM_COMMAND:
        handle_tray_command(int(w_param) & 0xFFFF)
        return 0

    if msg == WM_DESTROY:
        remove_native_tray_icon()
        user32.PostQuitMessage(0)
        return 0

    return user32.DefWindowProcW(hwnd, msg, w_param, l_param)


# 트레이 아이콘 전용 메시지 루프를 별도 데몬 스레드에서 실행합니다.
def start_tray_icon():
    def tray_thread():
        global tray_hwnd, tray_wndproc_ref
        h_instance = kernel32.GetModuleHandleW(None)
        tray_wndproc_ref = WNDPROC(tray_window_proc)

        window_class = WNDCLASSW()
        window_class.lpfnWndProc = tray_wndproc_ref
        window_class.hInstance = h_instance
        window_class.lpszClassName = TRAY_CLASS_NAME
        user32.RegisterClassW(ctypes.byref(window_class))

        tray_hwnd = user32.CreateWindowExW(
            0,
            TRAY_CLASS_NAME,
            TRAY_CLASS_NAME,
            0,
            0,
            0,
            0,
            0,
            None,
            None,
            h_instance,
            None,
        )
        if not tray_hwnd:
            return

        add_native_tray_icon(tray_hwnd)

        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    threading.Thread(target=tray_thread, daemon=True).start()

