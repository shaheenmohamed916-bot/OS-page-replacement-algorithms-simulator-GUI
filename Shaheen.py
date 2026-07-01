import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk


class PageReplacementEngines:
    @staticmethod
    def run_lru(pages, num_frames):
        frames_history, faults_history, victim_history = [], [], []
        current_frames, recent_usage = [], []

        for page in pages:
            victim_index = -1
            if page in current_frames:
                recent_usage.remove(page)
                recent_usage.append(page)
                is_fault = False
            else:
                is_fault = True
                if len(current_frames) < num_frames:
                    current_frames.append(page)
                    recent_usage.append(page)
                else:
                    lru_page = recent_usage.pop(0)
                    victim_index = current_frames.index(lru_page)
                    current_frames[victim_index] = page
                    recent_usage.append(page)

            frames_history.append(list(current_frames))
            faults_history.append(is_fault)
            victim_history.append(victim_index)

        return frames_history, faults_history, victim_history

    @staticmethod
    def run_fifo(pages, num_frames):
        frames_history, faults_history, victim_history = [], [], []
        current_frames, fifo_queue = [], []

        for page in pages:
            victim_index = -1
            if page in current_frames:
                is_fault = False
            else:
                is_fault = True
                if len(current_frames) < num_frames:
                    current_frames.append(page)
                    fifo_queue.append(page)
                else:
                    fifo_page = fifo_queue.pop(0)
                    victim_index = current_frames.index(fifo_page)
                    current_frames[victim_index] = page
                    fifo_queue.append(page)

            frames_history.append(list(current_frames))
            faults_history.append(is_fault)
            victim_history.append(victim_index)

        return frames_history, faults_history, victim_history

    @staticmethod
    def run_optimal(pages, num_frames):
        frames_history, faults_history, victim_history = [], [], []
        current_frames = []

        for i, page in enumerate(pages):
            victim_index = -1
            if page in current_frames:
                is_fault = False
            else:
                is_fault = True
                if len(current_frames) < num_frames:
                    current_frames.append(page)
                else:
                    max_future_index = -1
                    page_to_replace_idx = 0
                    for f_idx, f_page in enumerate(current_frames):
                        try:
                            future_idx = pages[i + 1:].index(f_page)
                        except ValueError:
                            future_idx = float('inf')
                        if future_idx > max_future_index:
                            max_future_index = future_idx
                            page_to_replace_idx = f_idx

                    victim_index = page_to_replace_idx
                    current_frames[victim_index] = page

            frames_history.append(list(current_frames))
            faults_history.append(is_fault)
            victim_history.append(victim_index)

        return frames_history, faults_history, victim_history


class MultiAlgorithmSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("OS Page Replacement Simulator - Full Background Edition")
        self.root.geometry("1020x750")

        # محاولة تحميل الصورة الخلفية
        try:
            self.bg_image_original = Image.open("IMG-20240709-WA0017.jpg")
        except Exception as e:
            print(f"Image not found: {e}")
            self.bg_image_original = None

        self.default_string = "7,0,1,2,0,3,0,4,2,3,0,3,0,3,2,1,2,0,1,7,0,1"
        self.pages = []
        self.num_frames = 3
        self.current_step = 0

        self.frames_history = []
        self.faults_history = []
        self.victim_history = []

        # Canvas يملأ كل النافذة - للصورة فقط
        self.bg_canvas = tk.Canvas(self.root, bd=0, highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # Frame شفاف فوق الصورة مباشرة - العناصر تطلع فوقها
        self.content_frame = tk.Frame(self.root)
        self.content_frame.place(x=0, y=0, relwidth=1, relheight=1)

        # ربط حدث تغيير حجم النافذة
        self.root.bind("<Configure>", self.on_window_resize)

        self.setup_ui()
        self.draw_background()

    def setup_ui(self):
        # إطار الإدخال
        input_frame = tk.LabelFrame(self.content_frame,
                                    text=" Simulation Settings ",
                                    font=("Helvetica", 10, "bold"),
                                    bg="#f0f0f0",
                                    fg="#34495e", padx=15, pady=10)
        input_frame.pack(fill="x", padx=15, pady=15)

        # اختيار الخوارزمية
        tk.Label(input_frame, text="Active Algorithm:",
                 bg="#f0f0f0",
                 font=("Helvetica", 9, "bold")).grid(row=0, column=0, sticky="w", pady=3)

        self.algo_combo = ttk.Combobox(input_frame,
                                       values=["LRU (Least Recently Used)",
                                               "FIFO (First-In First-Out)",
                                               "Optimal (OPT)"],
                                       state="readonly", width=25,
                                       font=("Helvetica", 9))
        self.algo_combo.current(0)
        self.algo_combo.grid(row=0, column=1, padx=10, pady=3, sticky="w")

        # إدخال String المراجع
        tk.Label(input_frame, text="Reference String:",
                 bg="#f0f0f0",
                 font=("Helvetica", 9)).grid(row=1, column=0, sticky="w", pady=3)

        self.str_entry = tk.Entry(input_frame, width=60, font=("Helvetica", 9), fg="gray")
        self.str_entry.insert(0, self.default_string)
        self.str_entry.grid(row=1, column=1, padx=10, pady=3, sticky="w")
        self.str_entry.bind("<FocusIn>", self.on_enter)
        self.str_entry.bind("<FocusOut>", self.on_leave)

        # عدد الإطارات
        tk.Label(input_frame, text="Frames (1-7):",
                 bg="#f0f0f0",
                 font=("Helvetica", 9)).grid(row=2, column=0, sticky="w", pady=3)

        self.frames_entry = tk.Entry(input_frame, width=8, font=("Helvetica", 9), fg="gray")
        self.frames_entry.insert(0, "3")
        self.frames_entry.grid(row=2, column=1, padx=10, pady=3, sticky="w")
        self.frames_entry.bind("<FocusIn>", self.on_frames_enter)
        self.frames_entry.bind("<FocusOut>", self.on_frames_leave)

        # أزرار التحكم
        btn_frame = tk.Frame(input_frame, bg="#f0f0f0")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)

        tk.Button(btn_frame, text="⚙️ Initialize Simulator", command=self.initialize_sim,
                  bg="#34495e", fg="white", font=("Helvetica", 9, "bold"), padx=10).pack(side="left", padx=3)

        self.prev_btn = tk.Button(btn_frame, text="⬅️ Prev", command=self.prev_step,
                                  bg="#e67e22", fg="white", font=("Helvetica", 9, "bold"),
                                  padx=10, state="disabled")
        self.prev_btn.pack(side="left", padx=3)

        self.next_btn = tk.Button(btn_frame, text="Next ➡️", command=self.next_step,
                                  bg="#2ecc71", fg="white", font=("Helvetica", 9, "bold"),
                                  padx=10, state="disabled")
        self.next_btn.pack(side="left", padx=3)

        self.comp_btn = tk.Button(btn_frame, text="📊 Show Quick Comparison",
                                  command=self.show_comparison,
                                  bg="#9b59b6", fg="white", font=("Helvetica", 9, "bold"),
                                  padx=10, state="disabled")
        self.comp_btn.pack(side="left", padx=3)

        # Canvas للمحاكاة (الشبكة)
        simulation_bg_frame = tk.Frame(self.content_frame, bg="#f0f0f0")
        simulation_bg_frame.pack(fill="x", padx=15, pady=10)

        self.simulation_canvas = tk.Canvas(simulation_bg_frame, height=180,
                                           bg="white", bd=1, relief="solid")
        self.simulation_canvas.pack(fill="x", padx=5, pady=5)

        # جدول المقارنة
        self.compare_frame = tk.LabelFrame(self.content_frame,
                                           text=" 📊 Live Multi-Algorithm Comparison Table ",
                                           font=("Helvetica", 10, "bold"),
                                           bg="#f0f0f0",
                                           fg="#2c3e50", pady=10)
        self.compare_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        headers = ["Algorithm", "Page Faults ❌", "Fault Ratio", "Page Hits ✅", "Hit Ratio"]
        for col_idx, text in enumerate(headers):
            lbl = tk.Label(self.compare_frame, text=text, font=("Helvetica", 9, "bold"),
                           bg="#dcdde1", fg="#2f3640", width=18, bd=1, relief="solid")
            lbl.grid(row=0, column=col_idx, padx=2, pady=2)

        self.rows_ui = {}
        algos_keys = ["LRU", "FIFO", "Optimal"]
        for row_idx, algo_name in enumerate(algos_keys, start=1):
            self.rows_ui[algo_name] = []
            lbl_name = tk.Label(self.compare_frame, text=algo_name,
                                font=("Helvetica", 9, "bold"),
                                bg="#f5f6fa", anchor="center", width=18, bd=1, relief="solid")
            lbl_name.grid(row=row_idx, column=0, padx=2, pady=2)

            for col_idx in range(1, 5):
                lbl_val = tk.Label(self.compare_frame, text="-", font=("Helvetica", 9),
                                   bg="white", width=18, bd=1, relief="solid")
                lbl_val.grid(row=row_idx, column=col_idx, padx=2, pady=1)
                self.rows_ui[algo_name].append(lbl_val)

        # تسمية الحالة
        self.status_lbl = tk.Label(self.content_frame,
                                   text="Select parameters and click 'Initialize'",
                                   font=("Helvetica", 10, "italic"),
                                   bg="#e8e8e8", fg="#7f8c8d", pady=3)
        self.status_lbl.pack(fill="x", padx=15)

    def on_window_resize(self, event):
        """رسم الخلفية عند تغيير حجم النافذة"""
        self.draw_background()

    def draw_background(self):
        """رسم صورة الخلفية - تملأ 100% من النافذة"""
        self.bg_canvas.delete("all")

        if self.bg_image_original:
            canvas_w = self.bg_canvas.winfo_width()
            canvas_h = self.bg_canvas.winfo_height()
            if canvas_w > 1 and canvas_h > 1:
                try:
                    resized = self.bg_image_original.resize((canvas_w, canvas_h),
                                                            Image.Resampling.LANCZOS)
                    self.root.canvas_bg_photo = ImageTk.PhotoImage(resized)
                    self.bg_canvas.create_image(0, 0, anchor="nw", image=self.root.canvas_bg_photo)
                except Exception as e:
                    print(f"Error resizing image: {e}")

    def on_enter(self, e):
        """حذف النص الافتراضي عند الضغط على حقل الإدخال"""
        if self.str_entry.cget("fg") == "gray":
            self.str_entry.delete(0, "end")
            self.str_entry.config(fg="black")

    def on_leave(self, e):
        """إعادة النص الافتراضي عند الخروج من الحقل"""
        if self.str_entry.get().strip() == "":
            self.str_entry.insert(0, self.default_string)
            self.str_entry.config(fg="gray")

    def on_frames_enter(self, e):
        """حذف النص الافتراضي عند الضغط على حقل الإطارات"""
        if self.frames_entry.cget("fg") == "gray":
            self.frames_entry.delete(0, "end")
            self.frames_entry.config(fg="black")

    def on_frames_leave(self, e):
        """إعادة النص الافتراضي عند الخروج من الحقل"""
        if self.frames_entry.get().strip() == "":
            self.frames_entry.insert(0, "3")
            self.frames_entry.config(fg="gray")

    def initialize_sim(self):
        """تهيئة المحاكاة"""
        if self.str_entry.cget("fg") == "gray" or self.frames_entry.cget("fg") == "gray":
            messagebox.showwarning("Warning",
                                   "Enter Number Of Frames and Reference String Correctly!")
            return

        try:
            raw_str = self.str_entry.get()
            self.pages = [int(x.strip()) for x in raw_str.split(",") if x.strip() != ""]
            self.num_frames = int(self.frames_entry.get())
            if self.num_frames <= 0 or self.num_frames > 7:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error",
                                 "Please enter a valid reference string and frames (1-7).")
            return

        self.current_step = 0
        selected_algo = self.algo_combo.get()

        if "LRU" in selected_algo:
            self.frames_history, self.faults_history, self.victim_history = \
                PageReplacementEngines.run_lru(self.pages, self.num_frames)
        elif "FIFO" in selected_algo:
            self.frames_history, self.faults_history, self.victim_history = \
                PageReplacementEngines.run_fifo(self.pages, self.num_frames)
        elif "Optimal" in selected_algo:
            self.frames_history, self.faults_history, self.victim_history = \
                PageReplacementEngines.run_optimal(self.pages, self.num_frames)

        self.next_btn.config(state="normal")
        self.prev_btn.config(state="disabled")
        self.comp_btn.config(state="normal")
        self.status_lbl.config(
            text=f"Ready! Simulating: {selected_algo.split(' ')[0]} | Click 'Next' or 'Show Quick Comparison'",
            fg="#2980b9")

        for algo in self.rows_ui:
            for cell in self.rows_ui[algo]:
                cell.config(text="-", bg="white")

        self.draw_grid()

    def show_comparison(self):
        """عرض المقارنة بين جميع الخوارزميات"""
        total_len = len(self.pages)
        if total_len == 0:
            return

        _, lru_faults_hist, _ = PageReplacementEngines.run_lru(self.pages, self.num_frames)
        lru_f = sum(1 for x in lru_faults_hist if x)
        lru_h = total_len - lru_f
        self.update_row_values("LRU", lru_f, f"{(lru_f / total_len) * 100:.1f}%", lru_h,
                               f"{(lru_h / total_len) * 100:.1f}%")

        _, fifo_faults_hist, _ = PageReplacementEngines.run_fifo(self.pages, self.num_frames)
        fifo_f = sum(1 for x in fifo_faults_hist if x)
        fifo_h = total_len - fifo_f
        self.update_row_values("FIFO", fifo_f, f"{(fifo_f / total_len) * 100:.1f}%", fifo_h,
                               f"{(fifo_h / total_len) * 100:.1f}%")

        _, opt_faults_hist, _ = PageReplacementEngines.run_optimal(self.pages, self.num_frames)
        opt_f = sum(1 for x in opt_faults_hist if x)
        opt_h = total_len - opt_f
        self.update_row_values("Optimal", opt_f, f"{(opt_f / total_len) * 100:.1f}%", opt_h,
                               f"{(opt_h / total_len) * 100:.1f}%")

        self.status_lbl.config(text="Comparison Table Updated for all 3 algorithms below! 📊",
                               fg="#27ae60")

    def update_row_values(self, algo_key, faults, f_ratio, hits, h_ratio):
        """تحديث قيم الصفوف في جدول المقارنة"""
        vals = [str(faults), f_ratio, str(hits), h_ratio]
        active_algo_short = self.algo_combo.get().split(' ')[0]
        bg_col = "#e8f4f8" if algo_key == active_algo_short or (
                algo_key == "Optimal" and active_algo_short == "Optimal") else "white"
        for idx, val in enumerate(vals):
            self.rows_ui[algo_key][idx].config(text=val, bg=bg_col)

    def draw_grid(self):
        """رسم شبكة المحاكاة"""
        self.simulation_canvas.delete("all")

        start_x, start_y, cell_size = 40, 10

        # رسم العناوين
        self.simulation_canvas.create_text(start_x + 50, start_y, text="Ref String:",
                                           font=("Helvetica", 9, "bold"), anchor="e", fill="black")
        for i in range(self.num_frames):
            self.simulation_canvas.create_text(start_x + 50, start_y + 35 + i * cell_size,
                                               text=f"Frame {i + 1}:",
                                               font=("Helvetica", 9, "bold"), anchor="e", fill="black")
        self.simulation_canvas.create_text(start_x + 50, start_y + 45 + self.num_frames * cell_size,
                                           text="Status:",
                                           font=("Helvetica", 9, "bold"), anchor="e", fill="black")

        # رسم الخطوات
        for step in range(self.current_step):
            x = start_x + 65 + step * (cell_size + 4)
            is_current = (step == self.current_step - 1)

            text_color = "#e74c3c" if is_current else "black"
            font_style = ("Helvetica", 10, "bold") if is_current else ("Helvetica", 9)
            self.simulation_canvas.create_text(x + cell_size / 2, start_y,
                                               text=str(self.pages[step]),
                                               font=font_style, fill=text_color)

            current_f = self.frames_history[step]
            victim_idx = self.victim_history[step]
            is_fault = self.faults_history[step]

            # رسم الإطارات
            for f_idx in range(self.num_frames):
                y = start_y + 18 + f_idx * cell_size
                bg_color = "#f1f2f6"

                if is_current:
                    if is_fault and f_idx == victim_idx:
                        bg_color = "#ffcccc"
                    elif not is_fault and f_idx < len(current_f) and \
                            current_f[f_idx] == self.pages[step]:
                        bg_color = "#d4edda"

                self.simulation_canvas.create_rectangle(x, y, x + cell_size, y + cell_size,
                                                        fill=bg_color, outline="#bdc3c7")

                if f_idx < len(current_f):
                    val_color = "#c0392b" if (is_current and is_fault and f_idx == victim_idx) \
                        else "black"
                    self.simulation_canvas.create_text(x + cell_size / 2, y + cell_size / 2,
                                                       text=str(current_f[f_idx]),
                                                       font=("Helvetica", 9, "bold"),
                                                       fill=val_color)

            # رسم حالة الفولت أو الهيت
            status_y = start_y + 35 + self.num_frames * cell_size
            status_text, status_color = ("F", "#e74c3c") if is_fault else ("H", "#2ecc71")
            self.simulation_canvas.create_text(x + cell_size / 2, status_y,
                                               text=status_text,
                                               font=("Helvetica", 10, "bold"),
                                               fill=status_color)

    def next_step(self):
        """الذهاب للخطوة التالية"""
        if self.current_step < len(self.pages):
            self.current_step += 1
            self.draw_grid()
            self.update_navigation_buttons()
            if self.current_step == len(self.pages):
                self.show_comparison()

    def prev_step(self):
        """الرجوع للخطوة السابقة"""
        if self.current_step > 0:
            self.current_step -= 1
            self.draw_grid()
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        """تحديث حالة أزرار التنقل"""
        self.prev_btn.config(state="disabled" if self.current_step == 0 else "normal")
        self.next_btn.config(state="disabled" if self.current_step == len(self.pages) else "normal")


if __name__ == "__main__":
    root = tk.Tk()
    app = MultiAlgorithmSimulator(root)


    def remove_focus(event):
        if event.widget == root or isinstance(event.widget, tk.Frame) or \
                isinstance(event.widget, tk.LabelFrame):
            root.focus_set()


    root.bind("<Button-1>", remove_focus)
    root.mainloop()
