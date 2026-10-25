import threading
import traceback
# Thư viện đã nén sẵn trong APK
import cv2  # opencv-python
import numpy as np  # numpy
import requests  # requests
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

# Đường dẫn Raw định tuyến cố định tới repository của bạn
GITHUB_RAW_URL = (
    "https://raw.githubusercontent.com/huyxaa06-hub/99999999/main/main.py"
)


class GitHubBridgeLoader(App):

  def build(self):
    self.title = "Auto Game Shell Loader"
    root = BoxLayout(orientation="vertical", padding=20, spacing=15)

    # --- Tiêu đề giao diện ---
    root.add_widget(
        Label(
            text="APK REMOTE LOADER",
            font_size=18,
            bold=True,
            color=(0, 1, 0, 1),
            size_hint_y=None,
            height=40,
        )
    )

    # --- Nhãn trạng thái ---
    self.status_label = Label(
        text="Trạng thái: Sẵn sàng kết nối GitHub",
        font_size=14,
        size_hint_y=None,
        height=30,
    )
    root.add_widget(self.status_label)

    # --- Nút thực thi ---
    self.action_btn = Button(
        text="Tải & Chạy main.py từ GitHub",
        background_color=(0, 0.7, 1, 1),
        font_size=16,
        bold=True,
        size_hint_y=None,
        height=50,
    )
    self.action_btn.bind(on_press=self.start_loading_process)
    root.add_widget(self.action_btn)

    # --- Khu vực hiển thị Log ---
    scroll = ScrollView(size_hint=(1, 1))
    self.log_label = Label(
        text=(
            "Đã định tuyến tới:\n->"
            f" {GITHUB_RAW_URL}\n\nNhấn nút bên trên để bắt đầu tải và thực"
            " thi...\n"
        ),
        size_hint_y=None,
        valign="top",
        halign="left",
    )
    self.log_label.bind(texture_size=lambda s, w: setattr(s, "height", w[1]))
    self.log_label.bind(width=lambda s, w: setattr(s, "text_size", (w, None)))
    scroll.add_widget(self.log_label)
    root.add_widget(scroll)

    return root

  def log(self, text):
    Clock.schedule_once(
        lambda dt: setattr(
            self.log_label, "text", self.log_label.text + "\n" + text
        )
    )

  def start_loading_process(self, instance):
    self.status_label.text = "Trạng thái: Đang kết nối..."
    self.action_btn.disabled = True
    # Chạy ngầm bằng Thread để tránh đơ giao diện Kivy
    threading.Thread(target=self.fetch_and_run_script, daemon=True).start()

  def fetch_and_run_script(self):
    try:
      self.log(f"[*] Đang tải nội dung từ GitHub...")
      response = requests.get(GITHUB_RAW_URL, timeout=10)

      if response.status_code == 200:
        script_code = response.text
        self.log("[+] Tải thành công! Đang khởi chạy trong môi trường APK...")
        self.status_label.text = "Trạng thái: Đang chạy script..."

        # Truyền các thư viện cốt lõi vào không gian thực thi từ xa
        global_namespace = {
            "__name__": "__main__",
            "cv2": cv2,
            "np": np,
            "requests": requests,
        }

        # Thực thi trực tiếp đoạn code tải về trong bộ nhớ
        exec(script_code, global_namespace)

        self.log("[+] Thực thi script hoàn tất!")
        self.status_label.text = "Trạng thái: Hoàn tất"
      else:
        self.log(f"[-] Lỗi tải file! Mã lỗi HTTP: {response.status_code}")
        self.status_label.text = "Trạng thái: Lỗi kết nối GitHub"

    except Exception as e:
      err_trace = traceback.format_exc()
      self.log(f"[-] Lỗi ngoại lệ:\n{err_trace}")
      self.status_label.text = "Trạng thái: Lỗi thực thi"
    finally:
      Clock.schedule_once(lambda dt: setattr(self.action_btn, "disabled", False))


if __name__ == "__main__":
  GitHubBridgeLoader().run()
