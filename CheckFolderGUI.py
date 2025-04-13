import sys
import time
import cv2
import numpy as np
from pathlib import Path
from functools import partial
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLabel, QProgressBar, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from SvgRenderer import get_check_svg_icon, set_svg_icon_from_string


class ImageChecker(QThread):
    progress_updated = pyqtSignal(int, str)
    checking_finished = pyqtSignal(bool, list)

    def __init__(self, folder_path, target_size=(640, 640)):
        super().__init__()
        self.folder_path = Path(folder_path)
        self.target_size = target_size
        self.valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}

    def read_image_with_cn_path(self, file_path):
        """解决中文路径问题"""
        try:
            with open(file_path, 'rb') as f:
                img_bytes = np.frombuffer(f.read(), dtype=np.uint8)
                return cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"读取文件失败: {file_path}, 错误: {str(e)}")
            return None

    def run(self):
        invalid_files = []
        image_files = [f for f in self.folder_path.iterdir()
                       if f.suffix.lower() in self.valid_extensions]
        total_files = len(image_files)

        for idx, file in enumerate(image_files, 1):
            try:
                img = self.read_image_with_cn_path(str(file))
                if img is None:
                    invalid_files.append((file.name, "无法读取"))
                    self.progress_updated.emit(int(idx / total_files * 100), f"检查: {file.name} (无法读取)")
                    continue

                h, w = img.shape[:2]
                if w != self.target_size[0] or h != self.target_size[1]:
                    invalid_files.append((file.name, f"{w}x{h}"))
                    self.progress_updated.emit(int(idx / total_files * 100), f"检查: {file.name} ({w}x{h})")
                else:
                    self.progress_updated.emit(int(idx / total_files * 100), f"检查: {file.name} (符合)")

            except Exception as e:
                invalid_files.append((file.name, f"错误: {str(e)}"))
                self.progress_updated.emit(int(idx / total_files * 100), f"检查: {file.name} (错误)")

        self.checking_finished.emit(len(invalid_files) == 0, invalid_files)


class ImageSizeCheckerApp(QMainWindow):
    def __init__(self, folder_path, callbacks):
        super().__init__()
        self.folder_path = folder_path
        self.start_time = time.time()
        self._all_ok = False
        self._c=True
        self._checking_completed = False  # 检查是否完成的标志
        self.callbacks = {
            'continue': callbacks.get('continue', lambda: None),
            'cancel': callbacks.get('cancel', lambda: None),
            'deal': callbacks.get('deal', lambda: None),
            'close': callbacks.get('close', lambda: None)
        }

        self.setWindowTitle("图片尺寸检查工具")
        self.setGeometry(100, 100, 500, 300)
        self.init_ui()
        self.start_countdown()

    def init_ui(self):
        main_widget = QWidget()
        layout = QVBoxLayout()

        self.folder_label = QLabel(f"检查文件夹: {self.folder_path}")
        self.folder_label.setWordWrap(True)
        layout.addWidget(self.folder_label)

        self.countdown_label = QLabel("2秒后开始自动检查...")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.countdown_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("准备开始检查...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
        set_svg_icon_from_string(self, get_check_svg_icon())

    def start_countdown(self):
        self.countdown = 2
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)

    def update_countdown(self):
        self.countdown -= 1
        if self.countdown > 0:
            self.countdown_label.setText(f"{self.countdown}秒后开始自动检查...")
        else:
            self.timer.stop()
            self.countdown_label.setText("正在开始检查...")
            self.start_checking()

    def start_checking(self):
        self.status_label.setText("正在检查图片尺寸...")
        self.progress_bar.setValue(0)

        self.checker = ImageChecker(self.folder_path)
        self.checker.progress_updated.connect(self.update_progress)
        self.checker.checking_finished.connect(self.show_result)
        self.checker.start()

    def update_progress(self, progress, status):
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)

    def show_result(self, all_valid, invalid_files):
        self.progress_bar.setValue(100)
        self._checking_completed = True  # 标记检查已完成

        if all_valid:
            QMessageBox.information(self, "检查完成", "所有图片都是640x640大小")
            self.callbacks['continue']()
            self._all_ok = True
            self.close()
        else:
            msg = "发现不符合640x640大小的图片:\n"
            for file, reason in invalid_files[:5]:
                msg += f"- {file}: {reason}\n"
            if len(invalid_files) > 5:
                msg += f"...(共{len(invalid_files)}个文件不符合)\n"

            msg_box = QMessageBox()
            msg_box.setWindowTitle("检查完成")
            msg_box.setText(msg + "\n发现有不符合尺寸的图片，请选择操作：")

            continue_btn = msg_box.addButton("继续", QMessageBox.YesRole)
            cancel_btn = msg_box.addButton("退出", QMessageBox.NoRole)
            deal_btn = msg_box.addButton("去处理", QMessageBox.HelpRole)

            msg_box.exec_()

            clicked_btn = msg_box.clickedButton()
            if clicked_btn == continue_btn:
                if self._c:
                    self.callbacks['continue']()
                self._all_ok = True
                self.close()
            elif clicked_btn == cancel_btn:
                self.callbacks['cancel']()
            elif clicked_btn == deal_btn:
                self.callbacks['deal']()
                self._all_ok = True
                self.close()

    def closeEvent(self, event):
        if not self._checking_completed:
            # 检查未完成时点击关闭按钮
            reply = QMessageBox.question(
                self, '确认关闭',
                '关闭会影响标注，确定继续吗?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.callbacks['continue']()
                self._c=False
                event.accept()
            else:
                event.ignore()
        else:
            # 检查已完成且有不合格图片时点击关闭按钮
            if not self._all_ok:
                self.callbacks['continue']()
            event.accept()


if __name__ == "__main__":
    def continue_callback():
        print("继续操作")


    def cancel_callback():
        print("取消操作")


    def deal_callback():
        print("去处理操作")


    def close_callback():
        print("关闭操作")


    app = QApplication(sys.argv)
    folder_path = "C:\\Users\\34859\\Pictures\\Screenshots"  # 替换为你的测试文件夹路径
    callbacks = {
        'continue': continue_callback,
        'cancel': cancel_callback,
        'deal': deal_callback,
        'close': close_callback
    }
    window = ImageSizeCheckerApp(folder_path, callbacks)
    window.show()
    sys.exit(app.exec_())
