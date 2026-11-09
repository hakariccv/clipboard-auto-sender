"""
хз спаммер крч который спамит там где есть текстовое поле.. типа дискорд, тг, майнкрафт чат??: вставка из буфера + Enter, настройка задержки.
запуск во python send_messages.py

"""

from __future__ import annotations

import ctypes
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    import pyautogui
    import pyperclip
except ImportError:
    raise SystemExit("Установи: pip install pyautogui pyperclip")

MESSAGES_FILE = Path(__file__).with_name("messages.txt")

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.02

VK_CONTROL = 0x11
VK_V = 0x56
KEYEVENTF_KEYUP = 0x0002
user32 = ctypes.windll.user32


def load_messages(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]


def paste_clipboard() -> None:
    """Ctrl+V через keybd_event — обычно Discord принимает."""
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    time.sleep(0.02)
    user32.keybd_event(VK_V, 0, 0, 0)
    time.sleep(0.02)
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.02)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)


def send_one(text: str) -> None:
    pyperclip.copy(text)
    time.sleep(0.06)
    paste_clipboard()
    time.sleep(0.12)
    pyautogui.press("enter")
    time.sleep(0.08)


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Discord Sender")
        self.geometry("520x460")
        self.minsize(480, 420)
        self.configure(bg="#1e1f22")

        self._stop = threading.Event()
        self._worker: threading.Thread | None = None
        self.file_path = tk.StringVar(value=str(MESSAGES_FILE))
        self.delay_sec = tk.DoubleVar(value=0.35)
        self.start_delay = tk.IntVar(value=5)
        self.status = tk.StringVar(value="Готов. Кликни в чат Discord и нажми Старт.")

        self._build()

    def _build(self) -> None:
        pad = {"padx": 14, "pady": 6}
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TLabel", background="#1e1f22", foreground="#dbdee1")
        style.configure("TFrame", background="#1e1f22")
        style.configure("TButton", padding=8)
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#ffffff")
        style.configure("Status.TLabel", foreground="#b5bac1")

        root = ttk.Frame(self)
        root.pack(fill="both", expand=True, **pad)

        ttk.Label(root, text="Discord Sender", style="Header.TLabel").pack(anchor="w", pady=(4, 10))

        file_row = ttk.Frame(root)
        file_row.pack(fill="x", pady=4)
        ttk.Label(file_row, text="Файл сообщений").pack(anchor="w")
        path_row = ttk.Frame(file_row)
        path_row.pack(fill="x", pady=2)
        ttk.Entry(path_row, textvariable=self.file_path).pack(side="left", fill="x", expand=True)
        ttk.Button(path_row, text="Обзор", command=self._browse, width=10).pack(side="left", padx=(8, 0))

        opts = ttk.Frame(root)
        opts.pack(fill="x", pady=10)

        left = ttk.Frame(opts)
        left.pack(side="left", fill="x", expand=True)
        ttk.Label(left, text="Задержка между сообщениями (сек)").pack(anchor="w")
        ttk.Spinbox(
            left,
            from_=0.05,
            to=30.0,
            increment=0.05,
            textvariable=self.delay_sec,
            width=10,
        ).pack(anchor="w", pady=2)

        right = ttk.Frame(opts)
        right.pack(side="left", fill="x", expand=True, padx=(16, 0))
        ttk.Label(right, text="Старт через (сек)").pack(anchor="w")
        ttk.Spinbox(
            right,
            from_=0,
            to=60,
            increment=1,
            textvariable=self.start_delay,
            width=10,
        ).pack(anchor="w", pady=2)

        btns = ttk.Frame(root)
        btns.pack(fill="x", pady=12)
        self.start_btn = ttk.Button(btns, text="Старт", command=self.start)
        self.start_btn.pack(side="left")
        self.stop_btn = ttk.Button(btns, text="Стоп", command=self.stop, state="disabled")
        self.stop_btn.pack(side="left", padx=(8, 0))

        ttk.Label(
            root,
            text="Перед стартом кликни в поле ввода Discord.\n"
            "Аварийный стоп: мышь в левый верхний угол экрана.",
            style="Status.TLabel",
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        ttk.Label(root, textvariable=self.status, style="Status.TLabel", wraplength=480).pack(
            anchor="w", fill="x"
        )

        log_frame = ttk.Frame(root)
        log_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.log = tk.Text(
            log_frame,
            height=12,
            bg="#2b2d31",
            fg="#dbdee1",
            insertbackground="#fff",
            relief="flat",
            font=("Consolas", 9),
            state="disabled",
        )
        scroll = ttk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _browse(self) -> None:
        path = filedialog.askopenfilename(
            title="Выбери txt",
            filetypes=[("Text", "*.txt"), ("All", "*.*")],
            initialdir=str(Path(self.file_path.get()).parent),
        )
        if path:
            self.file_path.set(path)

    def _log(self, text: str) -> None:
        def append() -> None:
            self.log.configure(state="normal")
            self.log.insert("end", text + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")

        self.after(0, append)

    def _set_status(self, text: str) -> None:
        self.after(0, lambda: self.status.set(text))

    def start(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        path = Path(self.file_path.get())
        try:
            messages = load_messages(path)
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))
            return
        if not messages:
            messagebox.showwarning("Пусто", "В файле нет сообщений")
            return

        self._stop.clear()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._log(f"--- Старт: {len(messages)} сообщений ---")
        self._worker = threading.Thread(target=self._run, args=(messages,), daemon=True)
        self._worker.start()

    def stop(self) -> None:
        self._stop.set()
        self._set_status("Останавливаю...")
        self._log("Стоп запрошен")

    def _finish_ui(self) -> None:
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    def _run(self, messages: list[str]) -> None:
        try:
            delay = max(0.05, float(self.delay_sec.get()))
            countdown = max(0, int(self.start_delay.get()))
        except (tk.TclError, ValueError):
            delay, countdown = 0.35, 5

        for remaining in range(countdown, 0, -1):
            if self._stop.is_set():
                self._set_status("Остановлено")
                self.after(0, self._finish_ui)
                return
            self._set_status(f"Кликни в Discord… старт через {remaining}с")
            time.sleep(1)

        self._set_status("Отправка...")

        for index, message in enumerate(messages, start=1):
            if self._stop.is_set():
                self._set_status("Остановлено")
                self._log("Остановлено пользователем")
                break

            preview = message if len(message) <= 70 else message[:67] + "..."
            self._set_status(f"[{index}/{len(messages)}] отправка...")
            self._log(f"[{index}/{len(messages)}] {preview}")

            try:
                send_one(message)
            except pyautogui.FailSafeException:
                self._set_status("Failsafe: мышь в углу")
                self._log("Остановлено failsafe")
                break
            except Exception as exc:
                self._set_status(f"Ошибка: {exc}")
                self._log(f"Ошибка: {exc}")
                break

            if index < len(messages) and not self._stop.is_set():
                # мелкими шагами, чтобы Стоп срабатывал быстрее
                end = time.time() + delay
                while time.time() < end:
                    if self._stop.is_set():
                        break
                    time.sleep(0.05)
        else:
            self._set_status("Готово")
            self._log("Готово")

        self.after(0, self._finish_ui)


if __name__ == "__main__":
    App().mainloop()
