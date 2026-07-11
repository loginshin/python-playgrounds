"""Tkinter help/practice window for the Windows app."""

import threading
import tkinter as tk

from .actions import open_url
from .config import APP_TITLE, BLOG_URL, GUI_SIZE, QUESTION_URL

gui_root = None
gui_lock = threading.Lock()


# Tkinter 도움말/연습 창을 띄우거나 이미 떠 있으면 앞으로 가져옵니다.
def show_help_gui():
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
            root.geometry(GUI_SIZE)
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
                "CapsLock + Space/Z/X/C/A/S/D/Q/W/E  =>  Numpad 0~9 키 입력",
                "CapsLock + J/K/L/I  =>  방향키",
                "CapsLock + H + J/L/I/K  =>  Home / End / PageUp / PageDown",
                "CapsLock + 방향키  =>  실제 방향키 입력",
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

