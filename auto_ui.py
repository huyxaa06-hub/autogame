import json
import os
import shutil
import subprocess
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

try:
  import cv2
  import numpy as np

  OPENCV_AVAILABLE = True
except ImportError:
  OPENCV_AVAILABLE = False


class ImageCropperWindow:

  def __init__(self, parent, cv_image, callback):
    self.top = tk.Toplevel(parent)
    self.top.title("Cắt Ảnh Mẫu (Kéo chuột khoanh vùng)")
    self.top.configure(bg="#121212")
    self.top.grab_set()

    self.original_image = cv_image
    self.callback = callback

    self.start_x = None
    self.start_y = None
    self.end_x = None
    self.end_y = None
    self.rect_id = None

    self.h, self.w = cv_image.shape[:2]
    self.max_w, self.max_h = 800, 600
    self.scale = 1.0
    if self.w > self.max_w or self.h > self.max_h:
      self.scale = min(self.max_w / self.w, self.max_h / self.h)
      self.display_img = cv2.resize(
          cv_image, (int(self.w * self.scale), int(self.h * self.scale))
      )
    else:
      self.display_img = cv_image

    self.disp_h, self.disp_w = self.display_img.shape[:2]

    rgb_img = cv2.cvtColor(self.display_img, cv2.COLOR_BGR2RGB)
    self.photo = tk.PhotoImage(
        data=cv2.imencode(".ppm", rgb_img)[1].tobytes()
    )

    top_bar = tk.Frame(self.top, bg="#1f1f1f", padx=5, pady=5)
    top_bar.pack(fill=tk.X, side=tk.TOP)

    tk.Label(
        top_bar,
        text=(
            "👉 Dùng chuột TRÁI kéo khoanh vùng vùng cần cắt làm ảnh mẫu, sau"
            " đó bấm Cắt & Lưu."
        ),
        font=("Arial", 9, "bold"),
        fg="#00adb5",
        bg="#1f1f1f",
    ).pack(side=tk.LEFT, padx=5)

    btn_crop = tk.Button(
        top_bar,
        text="✂️ Cắt & Lưu Ảnh Mẫu",
        command=self.confirm_crop,
        bg="#4CAF50",
        fg="white",
        font=("Arial", 9, "bold"),
        relief=tk.FLAT,
    )
    btn_crop.pack(side=tk.RIGHT, padx=5)

    self.canvas = tk.Canvas(
        self.top,
        width=self.disp_w,
        height=self.disp_h,
        cursor="cross",
        bg="#121212",
        highlightthickness=0,
    )
    self.canvas.pack(padx=10, pady=10)
    self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

    self.canvas.bind("<ButtonPress-1>", self.on_button_press)
    self.canvas.bind("<B1-Motion>", self.on_move_press)

  def on_button_press(self, event):
    self.start_x = event.x
    self.start_y = event.y
    if self.rect_id:
      self.canvas.delete(self.rect_id)
    self.rect_id = self.canvas.create_rectangle(
        self.start_x,
        self.start_y,
        1,
        1,
        outline="#ff5722",
        width=2,
        dash=(4, 4),
    )

  def on_move_press(self, event):
    self.end_x = event.x
    self.end_y = event.y
    self.canvas.coords(
        self.rect_id, self.start_x, self.start_y, self.end_x, self.end_y
    )

  def confirm_crop(self):
    if not self.start_x or not self.start_y or not self.end_x or not self.end_y:
      messagebox.showwarning(
          "Cảnh báo",
          "Vui lòng dùng chuột khoanh vùng trên ảnh trước!",
          parent=self.top,
      )
      return

    x1 = int(min(self.start_x, self.end_x) / self.scale)
    y1 = int(min(self.start_y, self.end_y) / self.scale)
    x2 = int(max(self.start_x, self.end_x) / self.scale)
    y2 = int(max(self.start_y, self.end_y) / self.scale)

    if x2 - x1 < 5 or y2 - y1 < 5:
      messagebox.showwarning(
          "Cảnh báo", "Vùng khoanh quá nhỏ!", parent=self.top
      )
      return

    cropped_img = self.original_image[y1:y2, x1:x2]
    self.top.destroy()
    self.callback(cropped_img)


class CoordinatePickerWindow:

  def __init__(self, parent, cv_image, callback):
    self.top = tk.Toplevel(parent)
    self.top.title("🎯 Bấm Chọn Vị Trí Cần Click")
    self.top.configure(bg="#121212")
    self.top.grab_set()

    self.original_image = cv_image
    self.callback = callback

    h, w = cv_image.shape[:2]
    self.max_w, self.max_h = 800, 600
    self.scale = 1.0
    if w > self.max_w or h > self.max_h:
      self.scale = min(self.max_w / w, self.max_h / h)
      self.display_img = cv2.resize(
          cv_image, (int(w * self.scale), int(h * self.scale))
      )
    else:
      self.display_img = cv_image

    disp_h, disp_w = self.display_img.shape[:2]

    rgb_img = cv2.cvtColor(self.display_img, cv2.COLOR_BGR2RGB)
    self.photo = tk.PhotoImage(
        data=cv2.imencode(".ppm", rgb_img)[1].tobytes()
    )

    top_bar = tk.Frame(self.top, bg="#1f1f1f", padx=5, pady=5)
    top_bar.pack(fill=tk.X, side=tk.TOP)

    tk.Label(
        top_bar,
        text="👉 Bấm chuột TRÁI vào vị trí bất kỳ trên màn hình để lấy tọa độ (X, Y).",
        font=("Arial", 9, "bold"),
        fg="#66fcf1",
        bg="#1f1f1f",
    ).pack(side=tk.LEFT, padx=5)

    self.canvas = tk.Canvas(
        self.top,
        width=disp_w,
        height=disp_h,
        cursor="target",
        bg="#121212",
        highlightthickness=0,
    )
    self.canvas.pack(padx=10, pady=10)
    self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

    self.canvas.bind("<Button-1>", self.on_canvas_click)

  def on_canvas_click(self, event):
    real_x = int(event.x / self.scale)
    real_y = int(event.y / self.scale)
    self.top.destroy()
    self.callback(real_x, real_y)


class AutoUIApp:

  def __init__(self, root):
    self.root = root
    self.root.title("🤖 Auto Macro Controller Pro")
    self.root.geometry("580x750")
    self.root.configure(bg="#121212")

    self.saved_file = "saved_apps.json"
    self.nicknames_file = "app_nicknames.json"
    self.configs_file = "app_auto_configs.json"
    self.saved_scripts_file = "saved_scripts_library.json"

    self.is_minimized = False
    self.is_auto_running = False
    self.active_auto_pkg = None

    self.offset_x = 0
    self.offset_y = 0

    self.menubar = tk.Menu(
        root, bg="#1f1f1f", fg="white", activebackground="#333333"
    )
    app_menu = tk.Menu(
        self.menubar,
        tearoff=0,
        bg="#1f1f1f",
        fg="white",
        activebackground="#00adb5",
    )
    app_menu.add_command(
        label="➕ Thêm ứng dụng từ máy",
        command=self.open_installed_apps_window,
    )
    app_menu.add_command(label="🔄 Làm mới danh sách", command=self.refresh_data)
    app_menu.add_separator()
    app_menu.add_command(
        label="🗕 Thu nhỏ thành thanh nổi", command=self.toggle_minimize_mode
    )
    self.menubar.add_cascade(label="⚙️ MENU AUTO", menu=app_menu)
    root.config(menu=self.menubar)

    self.main_frame = tk.Frame(root, bg="#121212")
    self.main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

    header_lbl = tk.Label(
        self.main_frame,
        text="⚡ BẢNG ĐIỀU KHIỂN MACRO & SCRIPT ⚡",
        font=("Arial", 11, "bold"),
        fg="#00adb5",
        bg="#121212",
    )
    header_lbl.pack(anchor="w", pady=(0, 6))

    search_frame = tk.Frame(self.main_frame, bg="#121212")
    search_frame.pack(fill=tk.X, pady=(0, 8))

    search_lbl = tk.Label(
        search_frame,
        text="🔍 Tìm kiếm:",
        font=("Arial", 9, "bold"),
        fg="#ffffff",
        bg="#121212",
    )
    search_lbl.pack(side=tk.LEFT, padx=(0, 5))

    self.search_var = tk.StringVar()
    # Đã sửa trace("w") thành trace_add("write") tương thích Tcl/Tk 9
    self.search_var.trace_add("write", lambda *args: self.refresh_data())

    self.search_entry = tk.Entry(
        search_frame,
        textvariable=self.search_var,
        font=("Consolas", 10),
        bg="#1e1e1e",
        fg="white",
        insertbackground="white",
        relief=tk.FLAT,
    )
    self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)

    manage_frame = tk.LabelFrame(
        self.main_frame,
        text=(
            " 🎮 DANH SÁCH ỨNG DỤNG (Bấm [⚙️ Cấu Hình] để lập trình & quản lý"
            " Script) "
        ),
        font=("Arial", 9, "bold"),
        fg="#ff5722",
        bg="#121212",
        bd=2,
        relief=tk.GROOVE,
    )
    manage_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    self.canvas = tk.Canvas(
        manage_frame, highlightthickness=0, bg="#1e1e1e"
    )
    self.scrollbar = ttk.Scrollbar(
        manage_frame, orient="vertical", command=self.canvas.yview
    )
    self.cards_frame = tk.Frame(self.canvas, bg="#1e1e1e")

    self.cards_frame.bind(
        "<Configure>",
        lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
    )
    self.canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
    self.canvas.configure(yscrollcommand=self.scrollbar.set)

    self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

    self.mini_frame = tk.Frame(root, bg="#1f2833", bd=2, relief=tk.RAISED)

    self.mini_header = tk.Label(
        self.mini_frame,
        text=" ⚡ MACRO CONTROLLER (Giữ kéo) ",
        bg="#0b0c10",
        fg="#66fcf1",
        font=("Arial", 9, "bold"),
        cursor="hand2",
    )
    self.mini_header.pack(fill=tk.X, padx=2, pady=2)
    self.mini_header.bind("<Button-1>", self.start_move)
    self.mini_header.bind("<B1-Motion>", self.do_move)

    mini_content = tk.Frame(self.mini_frame, bg="#1f2833")
    mini_content.pack(padx=6, pady=6, fill=tk.BOTH, expand=True)

    self.combo_mini = ttk.Combobox(
        mini_content, width=14, font=("Consolas", 9), state="readonly"
    )
    self.combo_mini.pack(side=tk.LEFT, padx=2)
    self.combo_mini.set("-- Chọn App --")

    self.btn_mini_open = tk.Button(
        mini_content,
        text="🚀 CHẠY",
        command=self.mini_open_app,
        bg="#45a29e",
        fg="#0b0c10",
        font=("Arial", 8, "bold"),
        relief=tk.FLAT,
    )
    self.btn_mini_open.pack(side=tk.LEFT, padx=2)

    self.btn_mini_stop = tk.Button(
        mini_content,
        text="⏹ DỪNG",
        command=self.stop_auto_task,
        bg="#F44336",
        fg="white",
        font=("Arial", 8, "bold"),
        relief=tk.FLAT,
    )
    self.btn_mini_stop.pack(side=tk.LEFT, padx=2)

    self.btn_expand = tk.Button(
        mini_content,
        text="🏠 MENU",
        command=self.toggle_minimize_mode,
        bg="#00adb5",
        fg="#121212",
        font=("Arial", 8, "bold"),
        relief=tk.FLAT,
    )
    self.btn_expand.pack(side=tk.LEFT, padx=2)

    if not OPENCV_AVAILABLE:
      messagebox.showwarning(
          "Thiếu thư viện",
          "Thư viện OpenCV (cv2) chưa được cài đặt!\nChạy lệnh: pip install"
          " opencv-python numpy",
      )

    self.refresh_data()

  def start_move(self, event):
    self.offset_x = event.x
    self.offset_y = event.y

  def do_move(self, event):
    x = self.root.winfo_x() + (event.x - self.offset_x)
    y = self.root.winfo_y() + (event.y - self.offset_y)
    self.root.geometry(f"+{x}+{y}")

  def toggle_minimize_mode(self):
    if not self.is_minimized:
      self.is_minimized = True
      self.main_frame.pack_forget()
      self.root.config(menu="")
      self.mini_frame.pack(fill=tk.BOTH, expand=True)

      self.root.overrideredirect(True)
      self.root.attributes("-topmost", True)
      self.root.geometry("400x75+100+100")
    else:
      self.is_minimized = False
      self.mini_frame.pack_forget()

      self.root.config(menu=self.menubar)
      self.main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

      self.root.overrideredirect(False)
      self.root.attributes("-topmost", False)
      self.root.geometry("580x750")

  def open_app_config_window(self, pkg_name, nick_name):
    cfg_win = tk.Toplevel(self.root)
    cfg_win.title(f"⚙️ Cấu Hình & Quản Lý Kịch Bản - {nick_name}")
    cfg_win.geometry("660x620")
    cfg_win.configure(bg="#121212")
    cfg_win.transient(self.root)
    cfg_win.grab_set()

    tk.Label(
        cfg_win,
        text=f"📌 Cấu Hình Kịch Bản Cho: {nick_name}",
        font=("Arial", 10, "bold"),
        fg="#00adb5",
        bg="#121212",
    ).pack(anchor="w", padx=12, pady=(10, 5))

    lib_bar = tk.Frame(cfg_win, bg="#1f1f1f", padx=5, pady=5)
    lib_bar.pack(fill=tk.X, padx=12, pady=(0, 5))

    def save_current_as_new_script():
      steps = []
      for item in tree.get_children():
        vals = tree.item(item, "values")
        steps.append({"type": vals[0], "target": vals[1], "delay": float(vals[2])})

      if not steps:
        messagebox.showwarning(
            "Cảnh báo",
            "Danh sách bước đang trống, không thể lưu kịch bản mới!",
            parent=cfg_win,
        )
        return

      script_name = simpledialog.askstring(
          "Lưu Kịch Bản Mới",
          "Nhập tên để lưu kịch bản này vào thư viện:",
          initialvalue=f"Script_{nick_name}_{int(time.time())}",
          parent=cfg_win,
      )
      if script_name:
        script_name = script_name.strip()
        if not script_name:
          return
        lib = self.load_scripts_library()
        lib[script_name] = {
            "steps": steps,
            "threshold": scale_threshold.get(),
        }
        self.save_scripts_library(lib)
        messagebox.showinfo(
            "Thành công",
            f"Đã lưu kịch bản mới [{script_name}] vào thư viện!",
            parent=cfg_win,
        )

    def load_old_script_from_library():
      lib = self.load_scripts_library()
      if not lib:
        messagebox.showinfo(
            "Thông báo",
            "Chưa có kịch bản cũ nào được lưu trong thư viện!",
            parent=cfg_win,
        )
        return

      sel_win = tk.Toplevel(cfg_win)
      sel_win.title("📂 Chọn Kịch Bản Cũ Đã Lưu")
      sel_win.geometry("400x300")
      sel_win.configure(bg="#121212")
      sel_win.transient(cfg_win)
      sel_win.grab_set()

      tk.Label(
          sel_win,
          text="Chọn kịch bản cũ để nạp vào:",
          font=("Arial", 9, "bold"),
          fg="#00adb5",
          bg="#121212",
      ).pack(pady=8)

      lb = tk.Listbox(
          sel_win,
          font=("Consolas", 10),
          bg="#1e1e1e",
          fg="white",
          selectbackground="#00adb5",
      )
      lb.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

      for sname in lib.keys():
        lb.insert(tk.END, sname)

      def confirm_load():
        selection = lb.curselection()
        if not selection:
          messagebox.showwarning(
              "Cảnh báo",
              "Vui lòng chọn một kịch bản trong danh sách!",
              parent=sel_win,
          )
          return
        chosen_name = lb.get(selection[0])
        sc_data = lib[chosen_name]

        for item in tree.get_children():
          tree.delete(item)

        scale_threshold.set(sc_data.get("threshold", 0.85))
        for step in sc_data.get("steps", []):
          new_item = tree.insert(
              "", tk.END, values=(step["type"], step["target"], step["delay"])
          )
          tree.see(new_item)

        sel_win.destroy()
        messagebox.showinfo(
            "Thành công",
            f"Đã nạp thành công kịch bản [{chosen_name}]!",
            parent=cfg_win,
        )

      tk.Button(
          sel_win,
          text="📥 Nạp Kịch Bản Này",
          command=confirm_load,
          bg="#4CAF50",
          fg="white",
          font=("Arial", 9, "bold"),
          relief=tk.FLAT,
      ).pack(pady=8, ipadx=5, ipady=3)

    tk.Button(
        lib_bar,
        text="💾 Lưu Thành Kịch Bản Mới",
        command=save_current_as_new_script,
        bg="#00adb5",
        fg="#121212",
        font=("Arial", 8, "bold"),
        relief=tk.FLAT,
    ).pack(side=tk.LEFT, padx=3)

    tk.Button(
        lib_bar,
        text="📂 Nạp Kịch Bản Cũ",
        command=load_old_script_from_library,
        bg="#ff5722",
        fg="white",
        font=("Arial", 8, "bold"),
        relief=tk.FLAT,
    ).pack(side=tk.LEFT, padx=3)

    macro_frame = tk.LabelFrame(
        cfg_win,
        text=" 📜 Danh Sách Bước Hành Động (Script) ",
        font=("Arial", 9, "bold"),
        fg="#ff5722",
        bg="#121212",
        bd=2,
        relief=tk.GROOVE,
    )
    macro_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=5)

    columns = ("type", "target", "delay")
    tree = ttk.Treeview(macro_frame, columns=columns, show="headings", height=8)
    tree.heading("type", text="Loại Thao Tác")
    tree.heading("target", text="Chi Tiết (Ảnh mẫu hoặc Tọa độ X, Y)")
    tree.heading("delay", text="Thời Gian Chờ (giây)")
    tree.column("type", width=120)
    tree.column("target", width=270)
    tree.column("delay", width=110)

    scrollbar = ttk.Scrollbar(
        macro_frame, orient="vertical", command=tree.yview
    )
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

    btn_bar = tk.Frame(cfg_win, bg="#121212")
    btn_bar.pack(fill=tk.X, padx=12, pady=5)

    def add_coord_step_by_picker():
      try:
        cfg_win.withdraw()
        time.sleep(0.3)
        screen_raw = subprocess.run(
            ["rish", "-c", "screencap -p"], capture_output=True, timeout=5
        )
        cfg_win.deiconify()

        if screen_raw.returncode != 0:
          messagebox.showerror("Lỗi", "Không thể chụp màn hình!", parent=cfg_win)
          return

        image_np = np.frombuffer(screen_raw.stdout, np.uint8)
        screen_img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        def save_picked_coord(x, y):
          coord_str = f"{x}, {y}"
          delay = simpledialog.floatdialog.askfloat(
              "Thời Gian Chờ",
              f"Đã lấy tọa độ ({coord_str}).\nNhập thời gian chờ sau khi click"
              " (giây):",
              initialvalue=1.0,
              minvalue=0.1,
              maxvalue=60.0,
              parent=cfg_win,
          )
          if delay is not None:
            new_item = tree.insert(
                "", tk.END, values=("Click Tọa Độ", coord_str, delay)
            )
            tree.see(new_item)

        CoordinatePickerWindow(cfg_win, screen_img, save_picked_coord)
      except Exception as e:
        cfg_win.deiconify()
        messagebox.showerror("Lỗi", f"{str(e)}", parent=cfg_win)

    def add_image_step():
      if not OPENCV_AVAILABLE:
        messagebox.showerror(
            "Lỗi", "Cần có OpenCV để dùng tính năng tìm ảnh!", parent=cfg_win
        )
        return
      try:
        cfg_win.withdraw()
        time.sleep(0.3)
        screen_raw = subprocess.run(
            ["rish", "-c", "screencap -p"], capture_output=True, timeout=5
        )
        cfg_win.deiconify()

        if screen_raw.returncode != 0:
          messagebox.showerror("Lỗi", "Không chụp được màn hình!", parent=cfg_win)
          return

        image_np = np.frombuffer(screen_raw.stdout, np.uint8)
        screen_img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        def save_cropped(cropped_img):
          if not os.path.exists("templates"):
            os.makedirs("templates")
          timestamp = int(time.time())
          file_path = os.path.abspath(f"templates/template_{timestamp}.png")
          cv2.imwrite(file_path, cropped_img)

          delay = simpledialog.floatdialog.askfloat(
              "Thời Gian Chờ",
              "Nhập thời gian chờ sau khi click trúng ảnh (giây):",
              initialvalue=1.0,
              minvalue=0.1,
              maxvalue=60.0,
              parent=cfg_win,
          )
          if delay is not None:
            new_item = tree.insert(
                "",
                tk.END,
                values=(
                    "Tìm Ảnh Mẫu",
                    os.path.basename(file_path),
                    delay,
                ),
            )
            tree.see(new_item)

        ImageCropperWindow(cfg_win, screen_img, save_cropped)
      except Exception as e:
        cfg_win.deiconify()
        messagebox.showerror("Lỗi", f"{str(e)}", parent=cfg_win)

    def load_image_from_pc():
      initial_dir = "/sdcard/DCIM"
      if not os.path.exists(initial_dir):
        initial_dir = "/sdcard/Pictures"
      if not os.path.exists(initial_dir):
        initial_dir = os.path.expanduser("~")

      file_path = filedialog.askopenfilename(
          title="Chọn ảnh mẫu từ Album điện thoại",
          initialdir=initial_dir,
          filetypes=[
              ("Image Files", "*.png *.jpg *.jpeg *.webp"),
              ("Tất cả file", "*.*"),
          ],
          parent=cfg_win,
      )
      if file_path:
        if not os.path.exists("templates"):
          os.makedirs("templates")

        filename = os.path.basename(file_path)
        dest_path = os.path.abspath(os.path.join("templates", filename))
        try:
          shutil.copy(file_path, dest_path)
        except Exception:
          dest_path = file_path

        delay = simpledialog.floatdialog.askfloat(
            "Thời Gian Chờ",
            "Nhập thời gian chờ sau khi click trúng ảnh (giây):",
            initialvalue=1.0,
            minvalue=0.1,
            maxvalue=60.0,
            parent=cfg_win,
        )
        if delay is not None:
          new_item = tree.insert(
              "",
              tk.END,
              values=("Tìm Ảnh Mẫu", os.path.basename(dest_path), delay),
          )
          tree.see(new_item)

    def edit_selected_step():
      selected = tree.selection()
      if not selected:
        messagebox.showwarning(
            "Cảnh báo",
            "Vui lòng chọn một bước trong danh sách để chỉnh sửa!",
            parent=cfg_win,
        )
        return
      item = selected[0]
      vals = tree.item(item, "values")
      stype, target, old_delay = vals[0], vals[1], float(vals[2])

      new_delay = simpledialog.floatdialog.askfloat(
          "Chỉnh Sửa Bước",
          f"Đang sửa bước: [{stype}]\nChi tiết: {target}\nNhập lại thời gian"
          " chờ (giây):",
          initialvalue=old_delay,
          minvalue=0.1,
          maxvalue=60.0,
          parent=cfg_win,
      )
      if new_delay is not None:
        tree.item(item, values=(stype, target, new_delay))

    def remove_step():
      selected_items = tree.selection()
      for item in selected_items:
        tree.delete(item)

    tk.Button(
        btn_bar,
        text="🎯 Lấy Tọa Độ",
        command=add_coord_step_by_picker,
        bg="#ff5722",
        fg="white",
        font=("Arial", 8, "bold"),
        relief=tk.FLAT,
    ).pack(side=tk.LEFT, padx=2)

    tk.Button(
        btn_bar,
        text="📷 Cắt Ảnh",
        command=add_image_step,
        bg="#45a29e",
        fg="#0b0c10",
        font=("Arial", 8, "bold"),
        relief=tk.FLAT,
    ).pack(side=tk.LEFT, padx=2)

    tk.Button(
        btn_bar,
        text="📁 Tải Ảnh",
        command=load_image_from_pc,
        bg="#00adb5",
        fg="#121212",
        font=("Arial", 8, "bold"),
        relief=tk.FLAT,
    ).pack(side=tk.LEFT, padx=2)

    tk.Button(
        btn_bar,
        text="✏️ Sửa Bước",
        command=edit_selected_step,
        bg="#393e46",
        fg="#ffeb3b",
        font=("Arial", 8, "bold"),
        relief=tk.FLAT,
    ).pack(side=tk.LEFT, padx=2)

    tk.Button(
        btn_bar,
        text="🗑️ Xóa Bước",
        command=remove_step,
        bg="#393e46",
        fg="#ff4757",
        font=("Arial", 8, "bold"),
        relief=tk.FLAT,
    ).pack(side=tk.LEFT, padx=2)

    thresh_frame = tk.Frame(cfg_win, bg="#121212")
    thresh_frame.pack(fill=tk.X, padx=12, pady=5)

    tk.Label(
        thresh_frame,
        text="Độ Khớp Ảnh (Threshold):",
        font=("Arial", 8),
        fg="white",
        bg="#121212",
    ).pack(side=tk.LEFT)
    scale_threshold = tk.Scale(
        thresh_frame,
        from_=0.6,
        to=0.98,
        resolution=0.01,
        orient=tk.HORIZONTAL,
        bg="#121212",
        fg="white",
        highlightbackground="#121212",
    )
    scale_threshold.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    def load_config():
      configs = self.load_configs_data()
      app_conf = configs.get(
          pkg_name, {"steps": [], "threshold": 0.85}
      )
      scale_threshold.set(app_conf.get("threshold", 0.85))
      for step in app_conf.get("steps", []):
        tree.insert(
            "", tk.END, values=(step["type"], step["target"], step["delay"])
        )

    load_config()

    def save_and_close():
      steps = []
      for item in tree.get_children():
        vals = tree.item(item, "values")
        steps.append({"type": vals[0], "target": vals[1], "delay": float(vals[2])})

      configs = self.load_configs_data()
      configs[pkg_name] = {"steps": steps, "threshold": scale_threshold.get()}
      self.save_configs_data(configs)
      cfg_win.destroy()
      messagebox.showinfo(
          "Thành công", f"Đã lưu cấu hình kịch bản cho [{nick_name}]!"
      )

    tk.Button(
        cfg_win,
        text="💾 Lưu & Đóng Cấu Hình",
        command=save_and_close,
        bg="#4CAF50",
        fg="white",
        font=("Arial", 9, "bold"),
        relief=tk.FLAT,
    ).pack(pady=8)

  def load_configs_data(self):
    if os.path.exists(self.configs_file):
      try:
        with open(self.configs_file, "r", encoding="utf-8") as f:
          return json.load(f)
      except Exception:
        return {}
    return {}

  def save_configs_data(self, data):
    with open(self.configs_file, "w", encoding="utf-8") as f:
      json.dump(data, f, ensure_ascii=False, indent=4)

  def load_scripts_library(self):
    if os.path.exists(self.saved_scripts_file):
      try:
        with open(self.saved_scripts_file, "r", encoding="utf-8") as f:
          return json.load(f)
      except Exception:
        return {}
    return {}

  def save_scripts_library(self, data):
    with open(self.saved_scripts_file, "w", encoding="utf-8") as f:
      json.dump(data, f, ensure_ascii=False, indent=4)

  def toggle_auto_for_app(self, pkg_name, nick_name):
    if not self.is_auto_running:
      configs = self.load_configs_data()
      app_conf = configs.get(pkg_name, {})
      if not app_conf.get("steps"):
        messagebox.showwarning(
            "Cảnh báo",
            f"Ứng dụng [{nick_name}] chưa có bước kịch bản nào!\nHãy bấm [⚙️"
            " Cấu Hình] để thêm bước trước.",
        )
        return

      self.is_auto_running = True
      self.active_auto_pkg = pkg_name
      threading.Thread(target=self._macro_execution_loop, daemon=True).start()
      self.refresh_data()
      if not self.is_minimized:
        self.toggle_minimize_mode()
    else:
      self.stop_auto_task()

  def stop_auto_task(self):
    self.is_auto_running = False
    self.active_auto_pkg = None
    self.refresh_data()
    messagebox.showinfo("Thông báo", "Đã dừng kịch bản Macro!")

  def _macro_execution_loop(self):
    while self.is_auto_running:
      try:
        configs = self.load_configs_data()
        app_conf = configs.get(self.active_auto_pkg, {})
        steps = app_conf.get("steps", [])
        threshold = app_conf.get("threshold", 0.85)

        if not steps:
          time.sleep(1)
          continue

        for step in steps:
          if not self.is_auto_running:
            break

          stype = step["type"]
          target = step["target"]
          delay = step["delay"]

          if stype == "Click Tọa Độ":
            try:
              parts = target.replace(" ", "").split(",")
              x, y = int(parts[0]), int(parts[1])
              subprocess.run(
                  ["rish", "-c", f"input tap {x} {y}"], capture_output=True
              )
              print(f"[{self.active_auto_pkg}] Script Click Tọa Độ ({x}, {y})")
            except Exception as e:
              print(f"Lỗi tọa độ: {e}")
            time.sleep(delay)

          elif stype == "Tìm Ảnh Mẫu":
            img_path = os.path.abspath(os.path.join("templates", target))
            if not os.path.exists(img_path):
              time.sleep(0.5)
              continue

            matched = False
            for _ in range(10):
              if not self.is_auto_running:
                break
              screen_raw = subprocess.run(
                  ["rish", "-c", "screencap -p"], capture_output=True, timeout=5
              )
              if screen_raw.returncode != 0:
                time.sleep(0.5)
                continue

              image_np = np.frombuffer(screen_raw.stdout, np.uint8)
              screen_img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
              template_img = cv2.imread(img_path, cv2.IMREAD_COLOR)

              if screen_img is None or template_img is None:
                break

              h_t, w_t = template_img.shape[:2]
              result = cv2.matchTemplate(
                  screen_img, template_img, cv2.TM_CCOEFF_NORMED
              )
              _, max_val, _, max_loc = cv2.minMaxLoc(result)

              if max_val >= threshold:
                center_x = max_loc[0] + w_t // 2
                center_y = max_loc[1] + h_t // 2
                subprocess.run(
                    ["rish", "-c", f"input tap {center_x} {center_y}"],
                    capture_output=True,
                )
                print(
                    f"[{self.active_auto_pkg}] Script Tìm Ảnh [{target}] tại"
                    f" ({center_x}, {center_y}) - Độ khớp: {max_val:.2f}"
                )
                matched = True
                break
              time.sleep(0.5)

            time.sleep(delay)

      except Exception as e:
        print(f"Lỗi Script Loop: {e}")
        time.sleep(1)

  def refresh_data(self):
    for widget in self.cards_frame.winfo_children():
      widget.destroy()

    saved_list = self.load_saved_choices()
    nicknames = self.load_nicknames()

    keyword = (
        self.search_var.get().lower().strip()
        if hasattr(self, "search_var")
        else ""
    )

    display_values = []
    self.pkg_mapping = {}

    for pkg in saved_list:
      nick = nicknames.get(pkg, pkg)

      if keyword and keyword not in nick.lower() and keyword not in pkg.lower():
        continue

      display_values.append(nick)
      self.pkg_mapping[nick] = pkg

      card = tk.Frame(
          self.cards_frame,
          bd=1,
          relief=tk.RAISED,
          bg="#252a34",
          padx=10,
          pady=8,
      )
      card.pack(fill=tk.X, expand=True, padx=6, pady=5)

      info_frame = tk.Frame(card, bg="#252a34")
      info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

      status_icon = (
          "🟢 [ĐANG CHẠY]"
          if (self.is_auto_running and self.active_auto_pkg == pkg)
          else "⚪"
      )
      lbl_nick = tk.Label(
          info_frame,
          text=f"{status_icon} {nick}",
          font=("Arial", 10, "bold"),
          fg="#00adb5" if self.active_auto_pkg != pkg else "#4CAF50",
          bg="#252a34",
          anchor="w",
      )
      lbl_nick.pack(fill=tk.X)

      lbl_pkg = tk.Label(
          info_frame,
          text=pkg,
          font=("Consolas", 8),
          fg="#aaaaaa",
          bg="#252a34",
          anchor="w",
      )
      lbl_pkg.pack(fill=tk.X)

      if self.is_auto_running and self.active_auto_pkg == pkg:
        btn_action = tk.Button(
            card,
            text="⏹ DỪNG",
            command=self.stop_auto_task,
            bg="#F44336",
            fg="white",
            font=("Arial", 8, "bold"),
            relief=tk.FLAT,
            width=7,
        )
      else:
        btn_action = tk.Button(
            card,
            text="⚡ CHẠY SCRIPT",
            command=lambda p=pkg, n=nick: self.run_app_and_auto(p, n),
            bg="#ff5722",
            fg="white",
            font=("Arial", 8, "bold"),
            relief=tk.FLAT,
            width=10,
        )
      btn_action.pack(side=tk.RIGHT, padx=2)

      btn_config = tk.Button(
          card,
          text="⚙️ Cấu Hình",
          command=lambda p=pkg, n=nick: self.open_app_config_window(p, n),
          bg="#00adb5",
          fg="#121212",
          font=("Arial", 8, "bold"),
          relief=tk.FLAT,
          width=8,
      )
      btn_config.pack(side=tk.RIGHT, padx=2)

      btn_del = tk.Button(
          card,
          text="🗑️ XÓA",
          command=lambda p=pkg: self.remove_app_by_pkg(p),
          bg="#393e46",
          fg="#ff4757",
          font=("Arial", 8, "bold"),
          relief=tk.FLAT,
          width=6,
      )
      btn_del.pack(side=tk.RIGHT, padx=2)

    if display_values:
      self.combo_mini["values"] = display_values
      if self.combo_mini.get() not in display_values:
        self.combo_mini.current(0)
    else:
      self.combo_mini["values"] = []
      self.combo_mini.set("-- Trống --")
      self.pkg_mapping = {}

  def run_app_and_auto(self, pkg_name, nick_name):
    threading.Thread(
        target=self._open_app_thread, args=(pkg_name,), daemon=True
    ).start()
    self.toggle_auto_for_app(pkg_name, nick_name)

  def mini_open_app(self):
    selected = self.combo_mini.get()
    if selected and selected in self.pkg_mapping:
      pkg_name = self.pkg_mapping[selected]
      nicknames = self.load_nicknames()
      self.run_app_and_auto(pkg_name, nicknames.get(pkg_name, pkg_name))

  def remove_app_by_pkg(self, pkg_to_remove):
    if self.is_auto_running and self.active_auto_pkg == pkg_to_remove:
      self.stop_auto_task()

    saved = self.load_saved_choices()
    if pkg_to_remove in saved:
      saved.remove(pkg_to_remove)
      with open(self.saved_file, "w", encoding="utf-8") as f:
        json.dump(saved, f, ensure_ascii=False, indent=4)

    nicknames = self.load_nicknames()
    if pkg_to_remove in nicknames:
      del nicknames[pkg_to_remove]
      with open(self.nicknames_file, "w", encoding="utf-8") as f:
        json.dump(nicknames, f, ensure_ascii=False, indent=4)

    configs = self.load_configs_data()
    if pkg_to_remove in configs:
      del configs[pkg_to_remove]
      self.save_configs_data(configs)

    self.refresh_data()
    messagebox.showinfo("Thành công", "Đã xóa ứng dụng khỏi danh sách!")

  def open_installed_apps_window(self):
    win = tk.Toplevel(self.root)
    win.title("Thêm Ứng Dụng Auto")
    win.geometry("520x570")
    win.configure(bg="#121212")
    win.transient(self.root)
    win.grab_set()

    action_btn_frame = tk.Frame(win, bg="#1f1f1f", padx=8, pady=8)
    action_btn_frame.pack(fill=tk.X, side=tk.TOP)

    sub_search_frame = tk.Frame(win, bg="#121212")
    sub_search_frame.pack(fill=tk.X, padx=8, pady=6)

    sub_search_lbl = tk.Label(
        sub_search_frame,
        text="🔍 Lọc app:",
        font=("Arial", 9, "bold"),
        fg="#ffffff",
        bg="#121212",
    )
    sub_search_lbl.pack(side=tk.LEFT, padx=(0, 5))

    sub_search_var = tk.StringVar()

    sub_search_entry = tk.Entry(
        sub_search_frame,
        textvariable=sub_search_var,
        font=("Consolas", 10),
        bg="#1e1e1e",
        fg="white",
        insertbackground="white",
        relief=tk.FLAT,
    )
    sub_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)

    app_list_cache = []

    def filter_sub_tree(*args):
      keyword = sub_search_var.get().lower().strip()
      for item in tree.get_children():
        tree.delete(item)
      for label, pkg in app_list_cache:
        if keyword in label.lower() or keyword in pkg.lower():
          tree.insert("", tk.END, values=(label, pkg))

    # Đã sửa trace("w") thành trace_add("write") tương thích Tcl/Tk 9
    sub_search_var.trace_add("write", filter_sub_tree)

    def add_selected():
      selected_item = tree.selection()
      if not selected_item:
        messagebox.showwarning(
            "Cảnh báo", "Vui lòng chọn một ứng dụng!", parent=win
        )
        return

      item_values = tree.item(selected_item, "values")
      default_label, pkg_name = item_values[0], item_values[1]

      nick = simpledialog.askstring(
          "Đặt tên gợi nhớ",
          f"Nhập tên hiển thị cho app:\n{pkg_name}",
          initialvalue=default_label,
          parent=win,
      )
      if nick is not None:
        final_nick = nick.strip() if nick.strip() else default_label

        saved = self.load_saved_choices()
        if pkg_name not in saved:
          saved.append(pkg_name)
          with open(self.saved_file, "w", encoding="utf-8") as f:
            json.dump(saved, f, ensure_ascii=False, indent=4)

        nicknames = self.load_nicknames()
        nicknames[pkg_name] = final_nick
        with open(self.nicknames_file, "w", encoding="utf-8") as f:
          json.dump(nicknames, f, ensure_ascii=False, indent=4)

        self.refresh_data()
        win.destroy()
        messagebox.showinfo(
            "Thành công", f"Đã thêm ứng dụng '{final_nick}' thành công!"
        )

    btn_add = tk.Button(
        action_btn_frame,
        text="➕ THÊM APP ĐÃ CHỌN",
        command=add_selected,
        bg="#00adb5",
        fg="#121212",
        font=("Arial", 9, "bold"),
        relief=tk.FLAT,
    )
    btn_add.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    btn_close_win = tk.Button(
        action_btn_frame,
        text="❌ ĐÓNG",
        command=win.destroy,
        bg="#393e46",
        fg="#ff4757",
        font=("Arial", 9, "bold"),
        relief=tk.FLAT,
    )
    btn_close_win.pack(side=tk.RIGHT, padx=5, expand=True, fill=tk.X)

    lbl = tk.Label(
        win,
        text="Đang quét danh sách ứng dụng hệ thống...",
        font=("Arial", 9, "italic"),
        fg="#00adb5",
        bg="#121212",
    )
    lbl.pack(pady=4)

    columns = ("label", "pkg")
    tree = ttk.Treeview(win, columns=columns, show="headings", height=13)
    tree.heading("label", text="Tên ứng dụng")
    tree.heading("pkg", text="Package Name")
    tree.column("label", width=180)
    tree.column("pkg", width=290)

    scrollbar = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=6)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=6)

    def load_apps_thread():
      nonlocal app_list_cache
      try:
        res = subprocess.run(
            ["rish", "-c", "pm list packages -3"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if res.returncode != 0:
          return
        pkgs = [
            line.replace("package:", "").strip()
            for line in res.stdout.splitlines()
            if line.startswith("package:")
        ]
        pkgs.sort()

        app_list = []
        for p in pkgs:
          d_res = subprocess.run(
              ["rish", "-c", f"dumpsys package {p}"],
              capture_output=True,
              text=True,
              timeout=3,
          )
          app_label = p
          for line in d_res.stdout.splitlines():
            if "application-label:" in line:
              app_label = line.split("application-label:")[-1].strip().strip("'")
              break
          app_list.append((app_label, p))

        app_list_cache = app_list

        def update_ui():
          lbl.config(text="Nhập từ khóa để lọc hoặc chọn ứng dụng bên dưới:")
          filter_sub_tree()

        win.after(0, update_ui)
      except Exception as e:
        win.after(0, lambda: lbl.config(text=f"Lỗi quét app: {str(e)}"))

    threading.Thread(target=load_apps_thread, daemon=True).start()

  def load_saved_choices(self):
    if os.path.exists(self.saved_file):
      try:
        with open(self.saved_file, "r", encoding="utf-8") as f:
          return json.load(f)
      except Exception:
        return []
    return []

  def load_nicknames(self):
    if os.path.exists(self.nicknames_file):
      try:
        with open(self.nicknames_file, "r", encoding="utf-8") as f:
          return json.load(f)
      except Exception:
        return {}
    return {}

  def _open_app_thread(self, pkg_name):
    try:
      cmd_fallback = f"am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p {pkg_name}"
      subprocess.run(
          ["rish", "-c", cmd_fallback], capture_output=True, text=True, timeout=10
      )
    except Exception:
      pass


if __name__ == "__main__":
  root = tk.Tk()
  app = AutoUIApp(root)
  root.mainloop()
