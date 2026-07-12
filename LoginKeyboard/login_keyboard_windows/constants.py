"""Windows virtual-key and Shell API constants used by LoGinKeyboard."""

VK_HANGUL = 0x15
VK_CAPITAL = 0x14
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1
VK_NUMLOCK = 0x90
VK_SCROLL = 0x91
VK_PRIOR = 0x21
VK_NEXT = 0x22
VK_END = 0x23
VK_HOME = 0x24
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_OEM_3 = 0xC0

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
WH_MOUSE_LL = 14
WM_LBUTTONDOWN = 0x0201
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
WM_DESTROY = 0x0002
WM_COMMAND = 0x0111
WM_USER = 0x0400
WM_TRAYICON = WM_USER + 20
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONUP = 0x0205
NIM_ADD = 0x00000000
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
IDI_APPLICATION = 32512
MF_STRING = 0x00000000
TPM_RIGHTBUTTON = 0x0002
TRAY_UID = 1
TRAY_OPEN_HELP = 1001
TRAY_OPEN_BLOG = 1002
TRAY_EXIT = 1003

NAVIGATION_VK = {
    "left": VK_LEFT,
    "right": VK_RIGHT,
    "up": VK_UP,
    "down": VK_DOWN,
    "home": VK_HOME,
    "end": VK_END,
    "page up": VK_PRIOR,
    "page down": VK_NEXT,
}

# IBM PC 키보드의 물리 넘버패드 숫자 위치에 해당하는 Set 1 스캔 코드입니다.
NUMPAD_SCAN_CODE = {
    "0": 0x52,
    "1": 0x4F,
    "2": 0x50,
    "3": 0x51,
    "4": 0x4B,
    "5": 0x4C,
    "6": 0x4D,
    "7": 0x47,
    "8": 0x48,
    "9": 0x49,
}

RIGHT_CTRL_NAVIGATION = {
    "right": "end",
    "left": "home",
    "up": "page up",
    "down": "page down",
}

CAPS_NAVIGATION_LAYER = {
    "i": ("up", "page up"),
    "j": ("left", "home"),
    "k": ("down", "page down"),
    "l": ("right", "end"),
}

NUMBER_LAYER = {
    "space": "0",
    "z": "1",
    "x": "2",
    "c": "3",
    "a": "4",
    "s": "5",
    "d": "6",
    "q": "7",
    "w": "8",
    "e": "9",
}

CAPS_ARROW_HOTKEYS = {
    "caps lock+up": "up",
    "caps lock+down": "down",
    "caps lock+left": "left",
    "caps lock+right": "right",
}
