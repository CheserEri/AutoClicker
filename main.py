"""
Auto Clicker - 简单的自动连点器
功能：可选择点击位置、设置点击间隔、开始/停止
"""

import sys
import os
import platform
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time


def check_environment():
    """启动时环境自检"""
    errors = []

    # 检查系统架构
    if platform.machine() not in ("AMD64", "x86_64", "x64"):
        errors.append("本程序仅支持64位Windows系统")

    # 检查VC++运行时 (Python 3.8 依赖 msvcr100/msvcp140)
    system32 = os.path.join(os.environ.get("SYSTEMROOT", r"C:\Windows"), "System32")
    if not os.path.exists(os.path.join(system32, "msvcp140.dll")):
        errors.append(
            "缺少 Visual C++ 运行时 (msvcp140.dll)\n\n"
            "解决方案:\n"
            "1. 运行「启动自动连点器.bat」自动修复\n"
            "2. 或手动安装 VC++ Redistributable:\n"
            "   https://aka.ms/vs/17/release/vc_redist.x64.exe"
        )

    return errors


def show_error_and_exit(title, message):
    """显示错误并退出"""
    # 尝试用tkinter显示，失败则用ctypes MessageBox
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    except Exception:
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)
    sys.exit(1)


# 启动前环境检查
_env_errors = check_environment()
if _env_errors:
    show_error_and_exit("自动连点器 - 环境错误", "\n\n".join(_env_errors))

import pyautogui
from pynput import keyboard

# 禁用 pyautogui 的安全暂停
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True


class AutoClicker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("自动连点器")
        self.root.geometry("400x350")
        self.root.resizable(False, False)

        # 状态变量
        self.clicking = False
        self.click_thread = None
        self.target_x = 0
        self.target_y = 0
        self.position_selected = False

        # 点击位置变量
        self.pos_x_var = tk.StringVar(value="未选择")
        self.pos_y_var = tk.StringVar(value="未选择")

        # 间隔变量
        self.interval_var = tk.StringVar(value="100")

        # 热键监听
        self.hotkey_listener = None

        self.setup_ui()
        self.setup_hotkey()

    def setup_ui(self):
        """设置界面"""
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text="自动连点器", font=("微软雅黑", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # 点击位置区域
        pos_frame = ttk.LabelFrame(main_frame, text="点击位置", padding="10")
        pos_frame.pack(fill=tk.X, pady=(0, 10))

        pos_info = ttk.Frame(pos_frame)
        pos_info.pack(fill=tk.X)

        ttk.Label(pos_info, text="X:").pack(side=tk.LEFT)
        ttk.Label(pos_info, textvariable=self.pos_x_var, width=8).pack(side=tk.LEFT, padx=(5, 15))
        ttk.Label(pos_info, text="Y:").pack(side=tk.LEFT)
        ttk.Label(pos_info, textvariable=self.pos_y_var, width=8).pack(side=tk.LEFT, padx=(5, 15))

        select_btn = ttk.Button(pos_info, text="选择位置", command=self.start_position_selection)
        select_btn.pack(side=tk.RIGHT)

        # 点击间隔区域
        interval_frame = ttk.LabelFrame(main_frame, text="点击间隔", padding="10")
        interval_frame.pack(fill=tk.X, pady=(0, 10))

        interval_info = ttk.Frame(interval_frame)
        interval_info.pack(fill=tk.X)

        ttk.Label(interval_info, text="间隔时间:").pack(side=tk.LEFT)
        interval_entry = ttk.Entry(interval_info, textvariable=self.interval_var, width=10)
        interval_entry.pack(side=tk.LEFT, padx=(10, 5))
        ttk.Label(interval_info, text="毫秒 (ms)").pack(side=tk.LEFT)

        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = ttk.Button(btn_frame, text="开始点击 (F6)", command=self.toggle_clicking)
        self.start_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        quit_btn = ttk.Button(btn_frame, text="退出", command=self.quit_app)
        quit_btn.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

        # 状态栏
        self.status_var = tk.StringVar(value="就绪 - 按 F6 开始/停止")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="gray")
        status_label.pack()

        # 提示
        tip_label = ttk.Label(main_frame, text="提示: 将鼠标移到目标位置后点击「选择位置」",
                              foreground="blue", font=("微软雅黑", 9))
        tip_label.pack(pady=(10, 0))

    def setup_hotkey(self):
        """设置键盘热键监听"""
        def on_press(key):
            if key == keyboard.Key.f6:
                self.root.after(0, self.toggle_clicking)

        self.hotkey_listener = keyboard.Listener(on_press=on_press)
        self.hotkey_listener.daemon = True
        self.hotkey_listener.start()

    def start_position_selection(self):
        """开始选择点击位置"""
        self.status_var.set("3秒后获取鼠标位置，请将鼠标移到目标位置...")
        self.root.update()

        # 延迟3秒后获取位置
        def get_position():
            time.sleep(3)
            x, y = pyautogui.position()
            self.target_x = x
            self.target_y = y
            self.position_selected = True
            self.root.after(0, lambda: self.update_position_display(x, y))

        threading.Thread(target=get_position, daemon=True).start()

    def update_position_display(self, x, y):
        """更新位置显示"""
        self.pos_x_var.set(str(x))
        self.pos_y_var.set(str(y))
        self.status_var.set(f"已选择位置: ({x}, {y})")

    def toggle_clicking(self):
        """切换点击状态"""
        if self.clicking:
            self.stop_clicking()
        else:
            self.start_clicking()

    def start_clicking(self):
        """开始点击"""
        if not self.position_selected:
            messagebox.showwarning("警告", "请先选择点击位置！")
            return

        try:
            interval_ms = int(self.interval_var.get())
            if interval_ms < 10:
                messagebox.showwarning("警告", "间隔不能小于10毫秒！")
                return
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字！")
            return

        self.clicking = True
        self.start_btn.config(text="停止点击 (F6)")
        self.status_var.set(f"正在点击 ({self.target_x}, {self.target_y})，间隔 {interval_ms}ms")

        # 启动点击线程
        self.click_thread = threading.Thread(
            target=self.click_loop,
            args=(interval_ms / 1000.0,),
            daemon=True
        )
        self.click_thread.start()

    def stop_clicking(self):
        """停止点击"""
        self.clicking = False
        self.start_btn.config(text="开始点击 (F6)")
        self.status_var.set("已停止")

    def click_loop(self, interval_sec):
        """点击循环"""
        while self.clicking:
            pyautogui.click(self.target_x, self.target_y)
            time.sleep(interval_sec)

    def quit_app(self):
        """退出应用"""
        self.clicking = False
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.root.quit()
        self.root.destroy()

    def run(self):
        """运行应用"""
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
        self.root.mainloop()


if __name__ == "__main__":
    app = AutoClicker()
    app.run()
