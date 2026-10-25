import threading
import traceback
# Các thư viện đã được nén sẵn trong APK sẽ hoạt động hoàn hảo ở đây:
import cv2  # opencv-python
import numpy as np  # numpy
import requests  # requests
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

# Đường dẫn Raw tới file code trên GitHub của bạn
GITHUB_RAW_URL = (
    "https://raw.githubusercontent.com/huyxaa06-hub/99999999/main/auto_ui.py"
)


class GithubRunnerApp(App):

  def build(self):
    self.title = "GitHub Python Runner"
    root = BoxLayout(orientation="vertical", padding=20, spacing=15)

    # Tiêu đề
    root.add_widget(
        Label(
            text="APP CHẠY PYTHON TỪ GITHUB",
            font_size=18,
            bold=True,
            color=(0, 1, 0, 1),
            size_hint_y=None,
            height=40,
        )
    )

    # Trạng thái
    self.status_label = Label(
        text="Trạng thái: Sẵn sàng tải và chạy code",
        font_size=14,
        size_hint_y=None,
        height=30,
    )
    root.add_widget(self.status_label)

    # Nút bấm thực thi
    self.run_btn = Button(
        text="Tải & Chạy Code Từ GitHub",
        background_color=(0, 0.7, 1, 1),
        font_size=16,
        bold=True,
        size_hint_y=None,
        height=50,
    )
    self.run_btn.bind(on_press=self.start_download_and_run)
    root.add_widget(self.run_btn)

    # Khung log hiển thị kết quả
    scroll = ScrollView(size_hint=(1, 1))
    self.log_label = Label(
        text="Bấm nút trên để tải và thực thi script trực tiếp...\n",
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

  def start_download_and_run(self, instance):
    self.status_label.text = "Trạng thái: Đang kết nối GitHub..."
    self.run_btn.disabled = True
    threading.Thread(target=self.fetch_and_execute, daemon=True).start()

  def fetch_and_execute(self):
    try:
      self.log("[*] Đang tải mã nguồn từ GitHub...")
      response = requests.get(GITHUB_RAW_URL, timeout=10)

      if response.status_code == 200:
        script_code = response.text
        self.log("[+] Tải thành công! Đang thực thi mã nguồn...")
        self.status_label.text = "Trạng thái: Đang chạy script..."

        # Tạo không gian tên riêng để chạy code tải về
        # Giúp script GitHub có thể import và dùng ngay requests, cv2, numpy đã có sẵn trong APK
        global_namespace = {
            "__name__": "__main__",
            "cv2": cv2,
            "np": np,
            "requests": requests,
        }

        # Thực thi code Python tải từ GitHub trực tiếp trong bộ nhớ
        exec(script_code, global_namespace)

        self.log("[+] Thực thi script hoàn tất!")
        self.status_label.text = "Trạng thái: Hoàn tất"
      else:
        self.log(f"[-] Lỗi tải file! Mã lỗi HTTP: {response.status_code}")
        self.status_label.text = "Trạng thái: Lỗi tải từ GitHub"

    except Exception as e:
      err_trace = traceback.format_exc()
      self.log(f"[-] Lỗi khi chạy code:\n{err_trace}")
      self.status_label.text = "Trạng thái: Lỗi thực thi"
    finally:
      Clock.schedule_once(lambda dt: setattr(self.run_btn, "disabled", False))


if __name__ == "__main__":
  GithubRunnerApp().run()
