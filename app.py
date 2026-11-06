import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from scipy.optimize import curve_fit

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


def logistic(t, r, K, N0):
    return K / (1 + (K - N0) / N0 * np.exp(-r * t))


def to_float(text):
    return float(text.strip().replace(",", "."))


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Логистическая модель роста числа предприятий")
        self.geometry("1200x700")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # ---------- левая панель ----------
        side = ctk.CTkFrame(self, width=290)
        side.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(side, text="Параметры модели",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        self.e_r = self.field(side, "r (темп роста, 1/год)", "0.1")
        self.e_K = self.field(side, "K (предел)", "250")
        self.e_N0 = self.field(side, "N0 (начальное число)", "100")
        self.e_T = self.field(side, "Период T (лет)", "25")

        ctk.CTkButton(side, text="Построить", command=self.build).pack(pady=10)

        ctk.CTkLabel(side, text="Реальные данные",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))
        ctk.CTkLabel(side, text="Значения по годам\n(через пробел, t = 0, 1, 2, ...)").pack()
        self.e_data = ctk.CTkEntry(side, width=250, placeholder_text="100 106 112 118")
        self.e_data.pack(pady=5)
        ctk.CTkButton(side, text="Загрузить из файла",
                      command=self.load_file).pack(pady=3)
        ctk.CTkButton(side, text="Подобрать r и K по данным",
                      command=self.fit).pack(pady=3)

        self.info = ctk.CTkLabel(side, text="", wraplength=260, justify="left")
        self.info.pack(pady=10)

        # ---------- график ----------
        right = ctk.CTkFrame(self)
        right.pack(side="right", fill="both", expand=True, padx=(0, 10), pady=10)

        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        NavigationToolbar2Tk(self.canvas, right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.build()

    def field(self, parent, text, default):
        ctk.CTkLabel(parent, text=text).pack(pady=(6, 0))
        e = ctk.CTkEntry(parent, width=150)
        e.insert(0, default)
        e.pack()
        return e

    def read_params(self):
        try:
            r = to_float(self.e_r.get())
            K = to_float(self.e_K.get())
            N0 = to_float(self.e_N0.get())
            T = int(to_float(self.e_T.get()))
        except ValueError:
            messagebox.showerror("Ошибка", "Во все поля нужно ввести числа")
            return None
        if r <= 0 or K <= 0 or N0 <= 0 or T < 1:
            messagebox.showerror("Ошибка", "r, K, N0 должны быть больше 0, T не меньше 1")
            return None
        return r, K, N0, T

    def read_data(self):
        text = self.e_data.get().replace(";", " ").replace("\n", " ")
        if not text.strip():
            return None
        try:
            return np.array([to_float(x) for x in text.split()])
        except ValueError:
            messagebox.showerror("Ошибка", "В данных должны быть только числа через пробел")
            return None

    def build(self):
        params = self.read_params()
        if params is None:
            return
        r, K, N0, T = params
        t = np.arange(T + 1)
        N = logistic(t, r, K, N0)

        self.ax.clear()
        self.ax.plot(t, N, "o-", label="Модель N(t)")
        self.ax.axhline(K, color="green", linestyle="--", label=f"K = {K:g}")

        y = self.read_data()
        if y is not None:
            self.ax.plot(np.arange(len(y)), y, "ro", markersize=7, label="Данные")

        self.ax.set_xlabel("Время, лет")
        self.ax.set_ylabel("Число предприятий")
        self.ax.set_title("Логистический рост числа предприятий")
        self.ax.grid(True)
        self.ax.legend()
        self.canvas.draw()

    def load_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Текстовые файлы", "*.txt *.csv"), ("Все файлы", "*.*")])
        if not path:
            return
        try:
            with open(path, encoding="utf-8-sig") as f:
                text = f.read()
            values = [to_float(x) for x in text.replace(";", " ").split()]
        except Exception:
            messagebox.showerror("Ошибка",
                                 "Не удалось прочитать файл.\n"
                                 "Нужны числа, разделённые пробелом, переводом строки или ;")
            return
        self.e_data.delete(0, "end")
        self.e_data.insert(0, " ".join(str(v) for v in values))
        self.build()

    def fit(self):
        y = self.read_data()
        if y is None or len(y) < 4:
            messagebox.showerror("Ошибка", "Для подгонки нужно минимум 4 значения данных")
            return
        t = np.arange(len(y))
        N0 = y[0]
        try:
            p, _ = curve_fit(lambda tt, r_, K_: logistic(tt, r_, K_, N0),
                             t, y, p0=[0.1, max(y) * 1.5],
                             bounds=([1e-6, 1e-6], [5, np.inf]), maxfev=10000)
        except Exception:
            messagebox.showerror("Ошибка", "Подобрать параметры не удалось")
            return
        r, K = p
        for e, v in ((self.e_r, f"{r:.4f}"), (self.e_K, f"{K:.1f}"), (self.e_N0, f"{N0:g}")):
            e.delete(0, "end")
            e.insert(0, v)
        self.info.configure(text=f"Подобрано: r = {r:.4f}, K = {K:.1f}, N0 = {N0:g}")
        self.build()

    def on_close(self):
        self.quit()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
