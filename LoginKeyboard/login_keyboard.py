r"""LoGinKeyboard 메인 프로그램.

이 앱은 Windows 전용 키보드 보조 유틸리티입니다.
- NumLock/CapsLock/ScrollLock 상태를 의도한 값으로 유지합니다.
- `keyboard` 패키지로 전역 단축키와 키 훅을 등록합니다.
- Tkinter로 도움말/연습 창을 표시합니다.
- Windows 트레이 아이콘으로 실행 상태 확인과 종료 메뉴를 제공합니다.

배포용 빌드 명령 예시:
    python -m PyInstaller --onefile --noconsole --name LoGinKeyboard-vX.Y.Z \
        --distpath releases\X.Y.Z --hidden-import keyboard \
        --hidden-import pyperclip --hidden-import pystray --hidden-import PIL \
        login_keyboard.py
"""

import ctypes
import ctypes.wintypes
import os
import sys
import threading
import time
import tkinter as tk
import webbrowser
from tkinter import messagebox
from urllib.parse import quote_plus

import keyboard
import pyperclip
import pystray
from PIL import Image, ImageDraw


APP_VERSION = "3.1.0"
APP_TITLE = f"LoGinKeyboard {APP_VERSION}"
BLOG_URL = "https://loginshin.tistory.com/17"
QUESTION_URL = "https://open.kakao.com/o/sVFNtrrf"

# ctypes로 Windows 키 상태와 훅을 다룰 때 사용하는 상수입니다.
VK_HANGUL = 0x15
VK_CAPITAL = 0x14
VK_NUMLOCK = 0x90
VK_SCROLL = 0x91
KEYEVENTF_KEYUP = 0x0002
WH_MOUSE_LL = 14
WM_LBUTTONDOWN = 0x0201
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# 런타임 공유 상태입니다. 키보드 훅과 트레이 콜백은 서로 다른 스레드에서
# 실행될 수 있으므로, 전역 상태는 작고 명확하게 유지합니다.
gui_root = None
gui_lock = threading.Lock()
tray_icon = None
caps_down_at = None
caps_combo_used = False
caps_h_prefix_down = False
mouse_proc_ref = None


def press_vk(vk_code):
    user32.keybd_event(vk_code, 0, 0, 0)
    user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)


def is_toggled(vk_code):
    return bool(user32.GetKeyState(vk_code) & 1)


def set_toggle_state(vk_code, enabled):
    if is_toggled(vk_code) != enabled:
        press_vk(vk_code)


def keep_lock_keys_stable():
    """키보드 레이어가 기대하는 Lock 키 상태를 적용합니다."""
    set_toggle_state(VK_NUMLOCK, True)
    set_toggle_state(VK_CAPITAL, False)
    set_toggle_state(VK_SCROLL, False)


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


def start_league_client_exit_hook():
    """League Client에서 왼쪽 클릭이 들어오면 앱을 즉시 종료합니다.

    기존 유틸리티의 동작을 맞춘 부분입니다. League Client를 사용할 때
    키보드 보조 기능이 남아 있지 않도록 합니다.
    """
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
                if foreground_process_name().lower() == "leagueclientux.exe":
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


def ensure_single_instance():
    """중복 키보드 훅을 막기 위해 앱을 한 번만 실행되게 합니다."""
    mutex_name = "Global\\LoGinKeyboardPython"
    handle = kernel32.CreateMutexW(None, False, mutex_name)
    if handle and kernel32.GetLastError() == 183:
        messagebox.showinfo("LoGinKeyboard", "LoGinKeyboard가 이미 실행 중입니다.")
        sys.exit(0)


def send_text(text):
    keyboard.write(text, delay=0)


def copy_selection():
    """현재 선택 영역을 복사한 뒤 검색/번역에 사용할 텍스트를 반환합니다."""
    keyboard.send("ctrl+c")
    time.sleep(0.08)
    return pyperclip.paste().strip()


def search_selected_text():
    text = copy_selection()
    if text:
        webbrowser.open(f"https://www.google.com/search?q={quote_plus(text)}")


def translate_selected_text():
    text = copy_selection()
    if text:
        url_text = quote_plus(text)
        webbrowser.open(
            f"https://translate.google.co.kr/?hl=ko&sl=auto&tl=ko&text={url_text}&op=translate"
        )


def open_url(url):
    webbrowser.open(url)


def create_tray_image():
    """외부 .ico 파일 없이 쓰도록 트레이 아이콘 이미지를 메모리에서 만듭니다."""
    image = Image.new("RGBA", (64, 64), (16, 20, 24, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 56, 56), radius=12, fill=(83, 209, 141, 255))
    draw.rectangle((18, 23, 46, 42), fill=(16, 20, 24, 255))
    draw.rectangle((22, 27, 27, 32), fill=(238, 243, 248, 255))
    draw.rectangle((30, 27, 35, 32), fill=(238, 243, 248, 255))
    draw.rectangle((38, 27, 43, 32), fill=(238, 243, 248, 255))
    draw.rectangle((22, 35, 43, 38), fill=(238, 243, 248, 255))
    return image


def quit_app(_icon=None, _item=None):
    """단축키나 트레이 메뉴에서 호출되어 훅/트레이를 정리하고 종료합니다."""
    global tray_icon
    try:
        keyboard.unhook_all()
    except Exception:
        pass

    if tray_icon is not None:
        try:
            tray_icon.stop()
        except Exception:
            pass
        tray_icon = None

    os._exit(0)


def start_tray_icon():
    """Windows 시스템 트레이 아이콘을 데몬 스레드에서 시작합니다."""
    def tray_thread():
        global tray_icon
        menu = pystray.Menu(
            pystray.MenuItem("LoGinKeyboard 실행 중", lambda: None, enabled=False),
            pystray.MenuItem("도움말 열기", lambda _icon, _item: show_help_gui()),
            pystray.MenuItem("블로그 열기", lambda _icon, _item: open_url(BLOG_URL)),
            pystray.MenuItem("종료", quit_app),
        )
        tray_icon = pystray.Icon("LoGinKeyboard", create_tray_image(), "LoGinKeyboard", menu)
        tray_icon.run()

    threading.Thread(target=tray_thread, daemon=True).start()


def show_help_gui():
    """항상 위에 표시되는 도움말/연습 창을 엽니다."""
    def build_gui():
        global gui_root
        with gui_lock:
            if gui_root is not None and gui_root.winfo_exists():
                gui_root.deiconify()
                gui_root.lift()
                gui_root.focus_force()
                return

            root = tk.Tk()
            gui_root = root

            root.title(APP_TITLE)
            root.geometry("1100x700")
            root.resizable(False, False)
            root.attributes("-topmost", True)
            root.overrideredirect(True)
            root.configure(bg="#101418")

            def close_gui():
                global gui_root
                root.destroy()
                gui_root = None

            root.protocol("WM_DELETE_WINDOW", close_gui)

            colors = {
                "bg": "#101418",
                "panel": "#171d24",
                "panel_alt": "#1d2530",
                "text": "#eef3f8",
                "muted": "#aeb9c6",
                "accent": "#53d18d",
                "accent_alt": "#7aa7ff",
                "danger": "#ff6b6b",
                "line": "#2c3744",
            }

            def label(parent, text, size=11, fg=None, bg=None, weight="normal", **place):
                widget = tk.Label(
                    parent,
                    text=text,
                    font=("Segoe UI", size, weight),
                    fg=fg or colors["text"],
                    bg=bg or colors["bg"],
                    anchor="w",
                    justify="left",
                )
                widget.place(**place)
                return widget

            def panel(x, y, w, h):
                frame = tk.Frame(root, bg=colors["panel"], highlightthickness=1, highlightbackground=colors["line"])
                frame.place(x=x, y=y, width=w, height=h)
                return frame

            def chip(parent, text, x, y, width=110):
                tk.Label(
                    parent,
                    text=text,
                    font=("Segoe UI", 10, "bold"),
                    fg=colors["bg"],
                    bg=colors["accent"],
                    padx=10,
                    pady=4,
                ).place(x=x, y=y, width=width, height=28)

            header = tk.Frame(root, bg=colors["panel_alt"])
            header.place(x=0, y=0, width=1100, height=105)
            label(header, "LoGinKeyboard", 24, colors["text"], colors["panel_alt"], "bold", x=42, y=22)
            label(
                header,
                "사용법 확인: RControl + CapsLock  |  프로그램 종료: LCtrl + LShift + Q",
                11,
                colors["muted"],
                colors["panel_alt"],
                x=46,
                y=66,
            )
            tk.Button(
                header,
                text="닫기",
                command=close_gui,
                font=("Segoe UI", 10, "bold"),
                fg=colors["text"],
                bg="#263140",
                activeforeground=colors["text"],
                activebackground="#344257",
                relief="flat",
                bd=0,
            ).place(x=1008, y=32, width=58, height=34)

            left = panel(38, 130, 492, 255)
            right = panel(570, 130, 492, 255)

            chip(left, "RControl", 24, 22)
            rcontrol_lines = [
                "RControl + ← / → / ↑ / ↓  =>  Home / End / PageUp / PageDown",
                "글씨 드래그 후 RControl + Enter  =>  구글 검색",
                "글씨 드래그 후 RControl + RShift  =>  한글로 번역",
            ]
            for idx, line in enumerate(rcontrol_lines):
                label(left, line, 12, colors["text"], colors["panel"], x=28, y=76 + idx * 48)

            chip(right, "CapsLock", 24, 22)
            caps_lines = [
                "CapsLock + Space/Z/X/C/A/S/D/Q/W/E  =>  숫자 출력",
                "CapsLock + J/K/L/I  =>  방향키",
                "CapsLock + H + J/L/I/K  =>  Home / End / PageUp / PageDown",
                "CapsLock + 방향키  =>  화살표 문자 ↑ ↓ ← →",
            ]
            for idx, line in enumerate(caps_lines):
                label(right, line, 12, colors["text"], colors["panel"], x=28, y=70 + idx * 42)

            practice = panel(38, 415, 655, 135)
            label(practice, "연습 입력창", 15, colors["accent_alt"], colors["panel"], "bold", x=28, y=22)
            label(practice, "아래 입력창에서 조합키 동작을 바로 확인해보세요.", 11, colors["muted"], colors["panel"], x=28, y=55)
            entry = tk.Entry(
                practice,
                width=32,
                font=("Segoe UI", 12),
                fg=colors["text"],
                bg="#0f141a",
                insertbackground=colors["text"],
                relief="flat",
            )
            entry.insert(0, "위에 단축키 연습해보세요")
            entry.place(x=28, y=88, width=590, height=34)

            warning = panel(725, 415, 337, 135)
            label(warning, "주의", 15, colors["danger"], colors["panel"], "bold", x=24, y=22)
            warning_lines = [
                "게임할 땐 꼭 이 프로그램을 꺼주세요.",
                "NumLock은 켜고, CapsLock/ScrollLock은 끕니다.",
                "CapsLock 자체는 CapsLock + Tab으로 토글합니다.",
            ]
            for idx, line in enumerate(warning_lines):
                label(warning, line, 10, colors["muted"], colors["panel"], x=24, y=58 + idx * 24)

            footer = tk.Frame(root, bg=colors["bg"])
            footer.place(x=38, y=590, width=1024, height=70)

            button_style = {
                "font": ("Segoe UI", 10, "bold"),
                "fg": colors["text"],
                "bg": "#263140",
                "activeforeground": colors["text"],
                "activebackground": "#344257",
                "relief": "flat",
                "bd": 0,
            }
            tk.Button(footer, text="부팅 시 실행하는 법", command=lambda: open_url(BLOG_URL), **button_style).place(
                x=0, y=10, width=150, height=38
            )
            tk.Button(footer, text="매크로 추가요청", command=lambda: open_url(QUESTION_URL), **button_style).place(
                x=164, y=10, width=140, height=38
            )
            tk.Button(footer, text="Thankyou LoGin", command=close_gui, **button_style).place(
                x=884, y=10, width=140, height=38
            )
            label(
                footer,
                "© copyright sign.신정환LoGinShin",
                9,
                colors["muted"],
                colors["bg"],
                x=650,
                y=20,
            )

            root.mainloop()

    threading.Thread(target=build_gui, daemon=True).start()


def toggle_capslock():
    press_vk(VK_CAPITAL)


def mark_caps_combo_used():
    global caps_combo_used
    caps_combo_used = True


def on_caps_down(_event):
    global caps_down_at, caps_combo_used
    caps_down_at = time.monotonic()
    caps_combo_used = False


def on_caps_up(_event):
    """CapsLock 단독 입력인지 조합 입력인지 확인한 뒤 동작을 결정합니다."""
    global caps_down_at, caps_combo_used, caps_h_prefix_down
    if caps_down_at is None:
        return

    held_for = time.monotonic() - caps_down_at
    caps_down_at = None
    caps_h_prefix_down = False

    if caps_combo_used:
        return
    if held_for >= 1:
        toggle_capslock()
    else:
        press_vk(VK_HANGUL)


def combo(action):
    def wrapped():
        mark_caps_combo_used()
        action()

    return wrapped


def send_key(key_name):
    mark_caps_combo_used()
    keyboard.send(key_name)


def handle_translate_shift(event):
    if event.event_type == "down" and keyboard.is_pressed("right ctrl"):
        translate_selected_text()
        return False
    return True


def caps_layer_active():
    """CapsLock이 커스텀 키보드 레이어로 동작 중이면 True를 반환합니다."""
    return caps_down_at is not None or keyboard.is_pressed("caps lock")


def handle_caps_layer_key(event, action):
    if not caps_layer_active():
        return True

    mark_caps_combo_used()
    if event.event_type == "down":
        action()
    return False


def handle_caps_h(event):
    global caps_h_prefix_down
    if not caps_layer_active():
        return True

    mark_caps_combo_used()
    caps_h_prefix_down = event.event_type == "down"
    return False


def handle_caps_navigation_key(event, normal_key, h_prefix_key):
    if not caps_layer_active():
        return True

    mark_caps_combo_used()
    if event.event_type == "down":
        keyboard.send(h_prefix_key if caps_h_prefix_down else normal_key)
    return False


def block_best_effort(*key_names):
    for key_name in key_names:
        try:
            keyboard.block_key(key_name)
        except Exception:
            pass


def register_hotkeys():
    """전역 단축키와 저수준 키 핸들러를 모두 등록합니다."""
    block_best_effort("hanja", "hangul", "scroll lock")

    keyboard.add_hotkey("right ctrl+caps lock", show_help_gui, suppress=True)
    keyboard.add_hotkey("right ctrl+right", lambda: keyboard.send("end"), suppress=True)
    keyboard.add_hotkey("right ctrl+left", lambda: keyboard.send("home"), suppress=True)
    keyboard.add_hotkey("right ctrl+up", lambda: keyboard.send("page up"), suppress=True)
    keyboard.add_hotkey("right ctrl+down", lambda: keyboard.send("page down"), suppress=True)
    keyboard.add_hotkey("right ctrl+enter", search_selected_text, suppress=True)
    keyboard.hook_key("right shift", handle_translate_shift, suppress=True)

    keyboard.add_hotkey("right shift+left shift+esc", lambda: send_text("`"), suppress=True)
    keyboard.add_hotkey("right shift+esc", lambda: send_text("~"), suppress=True)

    keyboard.on_press_key("caps lock", on_caps_down, suppress=True)
    keyboard.on_release_key("caps lock", on_caps_up, suppress=True)
    keyboard.add_hotkey("caps lock+tab", combo(toggle_capslock), suppress=True)

    keyboard.hook_key("h", handle_caps_h, suppress=True)
    keyboard.hook_key(
        "i",
        lambda event: handle_caps_navigation_key(event, "up", "page up"),
        suppress=True,
    )
    keyboard.hook_key(
        "j",
        lambda event: handle_caps_navigation_key(event, "left", "home"),
        suppress=True,
    )
    keyboard.hook_key(
        "k",
        lambda event: handle_caps_navigation_key(event, "down", "page down"),
        suppress=True,
    )
    keyboard.hook_key(
        "l",
        lambda event: handle_caps_navigation_key(event, "right", "end"),
        suppress=True,
    )

    number_layer = {
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
    for key, value in number_layer.items():
        keyboard.hook_key(
            key,
            lambda event, v=value: handle_caps_layer_key(event, lambda: keyboard.send(v)),
            suppress=True,
        )

    keyboard.add_hotkey("caps lock+esc", combo(lambda: send_text("`")), suppress=True)
    keyboard.add_hotkey("caps lock+up", combo(lambda: send_text("↑")), suppress=True)
    keyboard.add_hotkey("caps lock+down", combo(lambda: send_text("↓")), suppress=True)
    keyboard.add_hotkey("caps lock+left", combo(lambda: send_text("←")), suppress=True)
    keyboard.add_hotkey("caps lock+right", combo(lambda: send_text("→")), suppress=True)

    keyboard.add_hotkey("ctrl+shift+q", quit_app, suppress=True)


def main():
    """앱 시작 순서입니다."""
    ensure_single_instance()
    keep_lock_keys_stable()
    start_league_client_exit_hook()
    register_hotkeys()
    start_tray_icon()
    show_help_gui()
    keyboard.wait()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        messagebox.showerror("LoGinKeyboard", str(exc))
