import sys
import cv2
import numpy as np
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QFileDialog, QProgressBar,
                             QMessageBox, QCheckBox, QRadioButton, QButtonGroup, QColorDialog)
from PyQt5.QtGui import QIntValidator, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from SvgRenderer import get_deal_svg_icon, set_svg_icon_from_string


class ImageProcessor(QThread):
    progress_updated = pyqtSignal(int, str)
    finished_processing = pyqtSignal(int, int)

    def __init__(self, input_folder, output_folder, target_size, padding_color, output_format):
        super().__init__()
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.target_size = target_size
        self.padding_color = padding_color
        self.output_format = output_format
        self._is_running = True

    def run(self):
        if not self.input_folder.exists():
            self.progress_updated.emit(0, "❌ 输入文件夹不存在")
            return

        self.output_folder.mkdir(parents=True, exist_ok=True)

        image_files = [f for f in self.input_folder.glob('*')
                       if f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff')]
        total_files = len(image_files)
        processed_count = 0
        failed_count = 0

        for idx, file_path in enumerate(image_files, 1):
            if not self._is_running:
                break

            # 使用Path对象处理路径，避免编码问题
            output_path = self.output_folder / file_path.stem
            output_path = output_path.with_suffix(f'.{self.output_format.lower()}')

            processed = self.resize_with_padding(file_path)
            status = ""

            if processed is not None:
                try:
                    # 使用cv2.imencode + 文件操作代替imwrite
                    if self.output_format.lower() == 'jpg':
                        success, buf = cv2.imencode('.jpg', processed, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                    elif self.output_format.lower() == 'png':
                        success, buf = cv2.imencode('.png', processed, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])
                    else:
                        success, buf = cv2.imencode(f'.{self.output_format.lower()}', processed)

                    if success:
                        # 使用二进制写入模式保存文件
                        with open(str(output_path), 'wb') as f:
                            f.write(buf.tobytes())
                        processed_count += 1
                        status = f"✅ 已处理: {file_path.name}"
                    else:
                        failed_count += 1
                        status = f"❌ 编码失败: {file_path.name}"
                except Exception as e:
                    failed_count += 1
                    status = f"❌ 保存失败: {file_path.name} ({str(e)})"
            else:
                failed_count += 1
                status = f"❌ 处理失败: {file_path.name}"

            progress = int((idx / total_files) * 100)
            self.progress_updated.emit(progress, status)

        self.finished_processing.emit(processed_count, failed_count)

    def resize_with_padding(self, image_path):
        try:
            with open(image_path, 'rb') as f:
                img_bytes = np.frombuffer(f.read(), dtype=np.uint8)
                image = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)

            if image is None:
                return None

            h, w = image.shape[:2]
            target_w, target_h = self.target_size, self.target_size

            scale = min(target_w / w, target_h / h)
            new_w = int(w * scale)
            new_h = int(h * scale)

            resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.IMREAD_COLOR)
            canvas = np.full((target_h, target_w, 3), self.padding_color, dtype=np.uint8)

            x_offset = (target_w - new_w) // 2
            y_offset = (target_h - new_h) // 2

            canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
            return canvas
        except Exception:
            return None

    def stop(self):
        self._is_running = False


class ImageResizerApp(QMainWindow):
    def __init__(self, callbacks=lambda _dir: print(_dir), deal_dir=None):
        super().__init__()
        self.setWindowTitle("批量图片处理器")
        self.setGeometry(100, 100, 700, 500)
        self.callbacks = callbacks
        self.deal_dir = deal_dir
        self.init_ui()
        self.processor = None

    def init_ui(self):
        main_widget = QWidget()
        layout = QVBoxLayout()

        # 输入文件夹选择
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("输入文件夹:"))
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("点击浏览选择输入文件夹")

        if self.deal_dir is not None:
            self.input_line.setText(self.deal_dir)

        input_layout.addWidget(self.input_line)
        self.input_btn = QPushButton("浏览...")
        self.input_btn.clicked.connect(self.select_input_folder)
        input_layout.addWidget(self.input_btn)
        layout.addLayout(input_layout)

        # 输出文件夹选择
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出文件夹:"))
        self.output_line = QLineEdit()
        self.output_line.setPlaceholderText("点击浏览选择输出文件夹")

        if self.deal_dir is not None:
            self.output_line.setText(self.deal_dir + "_ok")

        output_layout.addWidget(self.output_line)
        self.output_btn = QPushButton("浏览...")
        self.output_btn.clicked.connect(self.select_output_folder)
        output_layout.addWidget(self.output_btn)
        layout.addLayout(output_layout)

        # 目标尺寸设置
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("目标尺寸:"))

        # 尺寸锁定按钮
        self.size_lock_btn = QPushButton("🔒")
        self.size_lock_btn.setCheckable(True)
        self.size_lock_btn.setChecked(True)
        self.size_lock_btn.setStyleSheet("QPushButton { max-width: 30px; }")
        self.size_lock_btn.clicked.connect(self.toggle_size_lock)
        size_layout.addWidget(self.size_lock_btn)

        self.size_input = QLineEdit("640")
        self.size_input.setValidator(QIntValidator(100, 4096))
        self.size_input.setMaximumWidth(80)
        self.size_input.setEnabled(False)  # 默认锁定
        size_layout.addWidget(self.size_input)
        size_layout.addWidget(QLabel("像素"))
        layout.addLayout(size_layout)

        # 填充颜色设置
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("填充颜色:"))

        # 颜色锁定按钮
        self.color_lock_btn = QPushButton("🔒")
        self.color_lock_btn.setCheckable(True)
        self.color_lock_btn.setChecked(True)
        self.color_lock_btn.setStyleSheet("QPushButton { max-width: 30px; }")
        self.color_lock_btn.clicked.connect(self.toggle_color_lock)
        color_layout.addWidget(self.color_lock_btn)

        self.color_input = QLineEdit("255,255,255")
        self.color_input.setMaximumWidth(100)
        self.color_input.setEnabled(False)  # 默认锁定
        color_layout.addWidget(self.color_input)

        self.color_picker_btn = QPushButton("选择颜色...")
        self.color_picker_btn.setEnabled(False)
        self.color_picker_btn.clicked.connect(self.pick_color)
        color_layout.addWidget(self.color_picker_btn)

        color_layout.addWidget(QLabel("(R,G,B)"))
        layout.addLayout(color_layout)

        # 输出格式设置
        format_layout = QVBoxLayout()
        format_layout.addWidget(QLabel("输出格式:"))

        # 格式单选按钮组
        self.format_group = QButtonGroup()

        format_radio_layout = QHBoxLayout()
        self.jpg_radio = QRadioButton("JPG")
        self.jpg_radio.setChecked(True)
        self.format_group.addButton(self.jpg_radio)
        format_radio_layout.addWidget(self.jpg_radio)

        self.png_radio = QRadioButton("PNG")
        self.format_group.addButton(self.png_radio)
        format_radio_layout.addWidget(self.png_radio)

        self.bmp_radio = QRadioButton("BMP")
        self.format_group.addButton(self.bmp_radio)
        format_radio_layout.addWidget(self.bmp_radio)

        self.custom_radio = QRadioButton("自定义:")
        self.format_group.addButton(self.custom_radio)
        format_radio_layout.addWidget(self.custom_radio)

        self.custom_format_input = QLineEdit()
        self.custom_format_input.setPlaceholderText("输入格式如webp")
        self.custom_format_input.setMaximumWidth(80)
        self.custom_format_input.setEnabled(False)
        format_radio_layout.addWidget(self.custom_format_input)

        # 连接信号
        self.format_group.buttonToggled.connect(self.on_format_changed)

        format_layout.addLayout(format_radio_layout)
        layout.addLayout(format_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel("准备就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # 操作按钮
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始处理")
        self.start_btn.clicked.connect(self.start_processing)
        button_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)

        layout.addLayout(button_layout)

        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
        set_svg_icon_from_string(self, get_deal_svg_icon())

    def toggle_size_lock(self, checked):
        if checked:
            # 锁定尺寸
            self.size_input.setEnabled(False)
            self.size_lock_btn.setText("🔒")
        else:
            # 解锁尺寸
            reply = QMessageBox.question(
                self, '警告',
                '更改目标尺寸可能影响标注工具的使用！\n确定要解锁吗？',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.size_input.setEnabled(True)
                self.size_lock_btn.setText("🔓")
            else:
                self.size_lock_btn.setChecked(True)

    def toggle_color_lock(self, checked):
        if checked:
            # 锁定颜色
            self.color_input.setEnabled(False)
            self.color_picker_btn.setEnabled(False)
            self.color_lock_btn.setText("🔒")
        else:
            # 解锁颜色
            reply = QMessageBox.question(
                self, '警告',
                '更改填充颜色可能影响模型训练效果！\n确定要解锁吗？',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.color_input.setEnabled(True)
                self.color_picker_btn.setEnabled(True)
                self.color_lock_btn.setText("🔓")
            else:
                self.color_lock_btn.setChecked(True)

    def pick_color(self):
        current_color = self.color_input.text().split(',')
        if len(current_color) == 3:
            color = QColorDialog.getColor(QColor(*map(int, current_color)), self, "选择填充颜色")
        else:
            color = QColorDialog.getColor(QColor(255, 255, 255), self, "选择填充颜色")

        if color.isValid():
            self.color_input.setText(f"{color.red()},{color.green()},{color.blue()}")

    def on_format_changed(self, button):
        if button == self.custom_radio:
            self.custom_format_input.setEnabled(True)
        else:
            self.custom_format_input.setEnabled(False)

    def select_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输入文件夹")
        if folder:
            self.input_line.setText(folder)

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.output_line.setText(folder)

    def validate_inputs(self):
        if not self.input_line.text():
            QMessageBox.warning(self, "警告", "请选择输入文件夹")
            return False

        if not self.output_line.text():
            QMessageBox.warning(self, "警告", "请选择输出文件夹")
            return False

        try:
            size = int(self.size_input.text())
            if size < 100 or size > 4096:
                raise ValueError
        except:
            QMessageBox.warning(self, "警告", "请输入有效的尺寸 (100-4096)")
            return False

        try:
            color = tuple(map(int, self.color_input.text().split(',')))
            if len(color) != 3 or any(c < 0 or c > 255 for c in color):
                raise ValueError
        except:
            QMessageBox.warning(self, "警告", "请输入有效的RGB颜色 (0-255,0-255,0-255)")
            return False

        # 验证输出格式
        if self.custom_radio.isChecked() and not self.custom_format_input.text().strip():
            QMessageBox.warning(self, "警告", "请输入自定义格式")
            return False

        return True

    def get_output_format(self):
        if self.jpg_radio.isChecked():
            return "jpg"
        elif self.png_radio.isChecked():
            return "png"
        elif self.bmp_radio.isChecked():
            return "bmp"
        else:
            return self.custom_format_input.text().strip().lower()

    def start_processing(self):
        if not self.validate_inputs():
            return

        input_folder = self.input_line.text()
        output_folder = self.output_line.text()
        target_size = int(self.size_input.text())
        padding_color = tuple(map(int, self.color_input.text().split(',')))
        output_format = self.get_output_format()

        self.progress_bar.setValue(0)
        self.status_label.setText("正在处理...")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self.processor = ImageProcessor(input_folder, output_folder,
                                        target_size, padding_color, output_format)
        self.processor.progress_updated.connect(self.update_progress)
        self.processor.finished_processing.connect(self.finish_processing)
        self.processor.start()

    def get_input_folder(self):
        return self.input_line.text()

    def stop_processing(self):
        if self.processor and self.processor.isRunning():
            self.processor.stop()
            self.status_label.setText("处理已停止")
            self.stop_btn.setEnabled(False)
            self.start_btn.setEnabled(True)

    def update_progress(self, progress, status):
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)

    def finish_processing(self, success, failed):
        self.progress_bar.setValue(100)
        self.status_label.setText(f"处理完成! 成功: {success}, 失败: {failed}")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.callbacks(self.output_line.text())
        self.close()
        if failed > 0:
            QMessageBox.information(self, "完成",
                                    f"处理完成!\n成功: {success}张\n失败: {failed}张",
                                    QMessageBox.Ok)

    def closeEvent(self, event):
        if self.processor and self.processor.isRunning():
            reply = QMessageBox.question(self, '确认退出',
                                         '处理仍在进行中，确定要退出吗?',
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.processor.stop()
                self.processor.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def A(dir):
    print(dir)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageResizerApp(callbacks=A)
    window.show()
    sys.exit(app.exec_())
