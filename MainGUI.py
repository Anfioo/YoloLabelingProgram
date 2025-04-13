import colorsys
import json
import os
import sys
from functools import partial
from time import sleep

import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QLabel,
                             QPushButton, QVBoxLayout, QWidget, QHBoxLayout,
                             QSpinBox, QComboBox, QSizePolicy, QMessageBox)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor

from CheckFolderGUI import ImageSizeCheckerApp
from SettingGUI import MainWindow
from ShowSelectGUI import ColorTextWindow

from SvgRenderer import get_main_svg_icon, set_svg_icon_from_string
from DealImagesGUI import ImageResizerApp


class LabelTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.create_success = False

        self.setWindowTitle("YOLO标注工具")
        self.setGeometry(100, 100, 400, 400)
        self._is_programmatic_change = False

        # 变量初始化
        self.image_dir = ""
        self.current_image = None
        self.image_path = ""
        self.drawing = False
        self.rect_start = QPoint()
        self.rect_end = QPoint()
        self.rectangles = []  # 存储所有标注框 [class_id, x1, y1, x2, y2]

        self.classes = []  # 默认类别
        self.classes_colors = []
        self.open_default_dir = ""
        self.config = None
        self.load_config()

        # 坐标转换参数
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.scaled_w = 0
        self.scaled_h = 0
        self.shortcuts = {}  # 存储快捷键配置
        self.load_shortcuts()  # 初始化时加载配置

        # UI初始化
        self.init_ui()
        self.setting_window = None
        self.color_show_window = None
        self.check_window = None
        self.deal_windows = None

        self.create_success = True

    def init_ui(self):
        # 主控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # 图像显示区域
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: black;")
        main_layout.addWidget(self.image_label, 1)

        # 控制面板
        control_panel = QWidget()
        control_layout = QHBoxLayout()
        control_panel.setLayout(control_layout)

        # 打开文件夹按钮
        self.open_btn = QPushButton("打开图片文件夹")
        self.open_btn.clicked.connect(self.open_image_dir)
        control_layout.addWidget(self.open_btn)

        # 上一张/下一张按钮
        self.prev_btn = QPushButton("上一张")
        self.prev_btn.clicked.connect(self.prev_image)
        control_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("下一张")
        self.next_btn.clicked.connect(self.next_image)
        control_layout.addWidget(self.next_btn)

        # 类别选择
        self.class_combo = QComboBox()
        self.class_combo.addItems(self.classes)
        self.class_combo.setStyleSheet("""
        QComboBox   {
            width: 50px;
                    }
        """)
        self.class_combo.currentIndexChanged.connect(self.on_combo_changed)
        control_layout.addWidget(QLabel("类别:"))
        control_layout.addWidget(self.class_combo)

        # 保存按钮
        self.save_btn = QPushButton("保存标注")
        self.save_btn.clicked.connect(self.save_labels)
        control_layout.addWidget(self.save_btn)

        # 删除最后一个框按钮
        self.del_btn = QPushButton("删除最后一个框")
        self.del_btn.clicked.connect(self.delete_last_rect)
        control_layout.addWidget(self.del_btn)

        # 删除最后一个框按钮
        self.setting_btn = QPushButton("设置")
        self.setting_btn.clicked.connect(self.open_setting)
        control_layout.addWidget(self.setting_btn)

        main_layout.addWidget(control_panel)
        set_svg_icon_from_string(self, get_main_svg_icon())
        # 状态栏
        self.statusBar().showMessage("准备就绪")

    def open_image_dir(self):
        """打开图片文件夹"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择图片文件夹", self.open_default_dir)
        if dir_path:
            self.check_window = ImageSizeCheckerApp(dir_path, {
                'continue': partial(self.open_image_dir_check_ok, dir_path),
                'cancel': lambda: sys.exit(),
                'deal': partial(self.deal_dir, dir_path),
                'close': self.show_exit_confirmation,
            })

            self.check_window.show()

    def show_exit_confirmation(self):
        """显示退出提示对话框（仅提示，不退出）"""
        QMessageBox.information(
            self,
            '操作取消',
            '取消操作可能会影响软件使用，请谨慎操作,并且仍然会在后台进行检查',
            QMessageBox.Ok
        )

    def open_image_dir_check_ok(self, dir_path):

        if dir_path:
            self.image_dir = dir_path
            self.image_files = [f for f in os.listdir(dir_path)
                                if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

            self.config["open_default_dir"] = dir_path
            self.open_default_dir = dir_path
            self.save_config()

            self.current_index = 0
            if self.image_files:
                self.load_image(os.path.join(dir_path, self.image_files[0]))
                self.statusBar().showMessage(f"已加载 {len(self.image_files)} 张图片")
            else:
                self.statusBar().showMessage("文件夹中没有图片文件")

        self.open_btn.setToolTip("快捷键：" + self.shortcuts["open_btn"])
        self.prev_btn.setToolTip("快捷键：" + self.shortcuts["prev_btn"])
        self.next_btn.setToolTip("快捷键：" + self.shortcuts["next_btn"])
        self.save_btn.setToolTip("快捷键：" + self.shortcuts["save_btn"])
        self.del_btn.setToolTip("快捷键：" + self.shortcuts["del_btn"])
        self.class_combo.setToolTip("快捷键：" + self.shortcuts["class_combo"] + " 循环选择")
        self.setting_btn.setToolTip("快捷键：" + self.shortcuts["setting_btn"])

        text_select, color_select, index_select = self.get_class_combo_select()
        if self.color_show_window is None:
            self.color_show_window = ColorTextWindow(bg_color=color_select, classes_text=text_select,
                                                     index=index_select)
        self.color_show_window.show()

    def on_combo_changed(self):
        if self._is_programmatic_change:
            return  # 程序触发的变更直接跳过
        text_select, color_select, index_select = self.get_class_combo_select()
        self.color_show_window.update_content(bg_color=color_select, classes_text=text_select, index=index_select)

    def load_image(self, image_path):
        """加载图片（修复版）"""
        self.image_path = image_path
        try:
            with open(image_path, 'rb') as f:
                img_bytes = bytearray(f.read())

            self.current_image = cv2.imdecode(np.asarray(img_bytes), cv2.IMREAD_COLOR)

            if self.current_image is None:
                raise ValueError("OpenCV无法解码图像")

            self.rectangles = []
            self.load_labels()
            self.show_image()

        except Exception as e:
            self.statusBar().showMessage(f"错误: {str(e)}")
            self.current_image = None
            error_img = np.zeros((500, 800, 3), dtype=np.uint8)
            cv2.putText(error_img, f"无法加载图片: {os.path.basename(image_path)}",
                        (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.putText(error_img, f"错误: {str(e)}", (50, 300),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1)

            h, w, ch = error_img.shape
            bytes_per_line = ch * w
            q_img = QImage(error_img.data, w, h, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            self.image_label.setPixmap(QPixmap.fromImage(q_img))

    def load_labels(self):
        """加载已有的YOLO格式标注文件"""
        label_path = self.get_label_path()
        if os.path.exists(label_path):
            with open(label_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 5:
                        class_id = int(parts[0])
                        x_center, y_center, width, height = map(float, parts[1:])

                        img_h, img_w = self.current_image.shape[:2]
                        x1 = (x_center - width / 2) * img_w
                        y1 = (y_center - height / 2) * img_h
                        x2 = (x_center + width / 2) * img_w
                        y2 = (y_center + height / 2) * img_h

                        self.rectangles.append([class_id, x1, y1, x2, y2])

    def get_label_path(self):
        """获取对应的标签文件路径"""
        base_name = os.path.splitext(os.path.basename(self.image_path))[0]
        dir_name = os.path.dirname(self.image_path)
        label_dir = os.path.join(dir_name, "../labels")
        os.makedirs(label_dir, exist_ok=True)
        return os.path.join(label_dir, f"{base_name}.txt")

    def next_class(self):
        """切换到下一个类别（循环）"""
        current_index = self.class_combo.currentIndex()
        next_index = (current_index + 1) % self.class_combo.count()  # 循环计算下一个索引
        self.class_combo.setCurrentIndex(next_index)

    def show_image(self):
        """显示图片和标注框（包含坐标转换参数计算）"""
        if self.current_image is not None:
            display_image = self.current_image.copy()

            # 绘制所有标注框
            for rect in self.rectangles:
                class_id, x1, y1, x2, y2 = rect

                cv2.rectangle(display_image, (int(x1), int(y1)), (int(x2), int(y2)), self.classes_colors[class_id], 2)

                cv2.putText(display_image, self.classes[class_id], (int(x1), int(y1) - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.classes_colors[class_id], 1)

            # 绘制当前框

            if self.drawing:
                x1, y1 = self.rect_start.x(), self.rect_start.y()
                x2, y2 = self.rect_end.x(), self.rect_end.y()
                cv2.rectangle(display_image, (x1, y1), (x2, y2), self.classes_colors[self.class_combo.currentIndex()],
                              2)

            # 转换为Qt格式
            h, w, ch = display_image.shape
            bytes_per_line = ch * w
            q_img = QImage(display_image.data, w, h, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_img)
            self.image_label.setPixmap(pixmap)

            # 计算坐标转换参数
            label_width = self.image_label.width()
            label_height = self.image_label.height()
            pixmap_width = pixmap.width()
            pixmap_height = pixmap.height()

            if pixmap_width > 0 and pixmap_height > 0:
                w_ratio = label_width / pixmap_width
                h_ratio = label_height / pixmap_height
                self.scale = min(w_ratio, h_ratio)
                self.scaled_w = pixmap_width * self.scale
                self.scaled_h = pixmap_height * self.scale
                self.offset_x = (label_width - self.scaled_w) / 2
                self.offset_y = (label_height - self.scaled_h) / 2
            else:
                self.scale = 1.0
                self.offset_x = 0
                self.offset_y = 0
                self.scaled_w = 0
                self.scaled_h = 0

    def mousePressEvent(self, event):
        """鼠标按下事件（带坐标转换）"""
        if event.button() == Qt.LeftButton and self.image_label.underMouse():
            pos_in_label = self.image_label.mapFromParent(event.pos())
            x = pos_in_label.x()
            y = pos_in_label.y()

            if (self.offset_x <= x <= self.offset_x + self.scaled_w and
                    self.offset_y <= y <= self.offset_y + self.scaled_h):
                img_x = (x - self.offset_x) / self.scale
                img_y = (y - self.offset_y) / self.scale
                pixmap = self.image_label.pixmap()
                if pixmap:
                    img_x = max(0, min(img_x, pixmap.width()))
                    img_y = max(0, min(img_y, pixmap.height()))
                    self.drawing = True
                    self.rect_start = QPoint(int(img_x), int(img_y))
                    self.rect_end = self.rect_start
                    self.show_image()

    def mouseMoveEvent(self, event):
        """鼠标移动事件（带坐标转换）"""
        if self.drawing and self.image_label.underMouse():
            pos_in_label = self.image_label.mapFromParent(event.pos())
            x = pos_in_label.x()
            y = pos_in_label.y()

            if (self.offset_x <= x <= self.offset_x + self.scaled_w and
                    self.offset_y <= y <= self.offset_y + self.scaled_h):
                img_x = (x - self.offset_x) / self.scale
                img_y = (y - self.offset_y) / self.scale
                pixmap = self.image_label.pixmap()
                if pixmap:
                    img_x = max(0, min(img_x, pixmap.width()))
                    img_y = max(0, min(img_y, pixmap.height()))
                    self.rect_end = QPoint(int(img_x), int(img_y))
                    self.show_image()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件（带坐标转换）"""
        if event.button() == Qt.LeftButton and self.drawing:
            pos_in_label = self.image_label.mapFromParent(event.pos())
            x = pos_in_label.x()
            y = pos_in_label.y()

            if (self.offset_x <= x <= self.offset_x + self.scaled_w and
                    self.offset_y <= y <= self.offset_y + self.scaled_h):
                img_x = (x - self.offset_x) / self.scale
                img_y = (y - self.offset_y) / self.scale
                pixmap = self.image_label.pixmap()
                if pixmap:
                    img_x = max(0, min(img_x, pixmap.width()))
                    img_y = max(0, min(img_y, pixmap.height()))
                    self.rect_end = QPoint(int(img_x), int(img_y))

                    if abs(self.rect_end.x() - self.rect_start.x()) > 10 and abs(
                            self.rect_end.y() - self.rect_start.y()) > 10:
                        class_id = self.class_combo.currentIndex()
                        x1 = min(self.rect_start.x(), self.rect_end.x())
                        y1 = min(self.rect_start.y(), self.rect_end.y())
                        x2 = max(self.rect_start.x(), self.rect_end.x())
                        y2 = max(self.rect_start.y(), self.rect_end.y())
                        self.rectangles.append([class_id, x1, y1, x2, y2])

                    self.drawing = False
                    self.show_image()

    def resizeEvent(self, event):
        """窗口大小改变时更新显示"""
        self.show_image()
        super().resizeEvent(event)

    def load_shortcuts(self):
        """加载快捷键配置"""
        try:
            with open('resource/shortcuts.json', 'r') as f:
                self.shortcuts = json.load(f)

        except (FileNotFoundError, json.JSONDecodeError):
            # 如果文件不存在或格式错误，使用默认配置
            self.shortcuts = {
                "open_btn": "Ctrl+O",
                "prev_btn": "Left",
                "next_btn": "Right",
                "save_btn": "Ctrl+S",
                "del_btn": "Ctrl+D",
                "setting_btn": "Ctrl+I",
                "class_combo": "Ctrl+Q"
            }
            # 可以保存默认配置到文件
            self.save_shortcuts()

    def load_config(self):
        """加载快捷键配置"""
        try:
            with open('resource/config.json', 'r') as f:
                self.config = json.load(f)

        except (FileNotFoundError, json.JSONDecodeError):
            # 如果文件不存在或格式错误，使用默认配置
            self.config = {
                "open_default_dir": "C:/Users",
                "classes": [
                    {
                        "label": "Category1",
                        "r": 255,
                        "g": 0,
                        "b": 0
                    },
                    {
                        "label": "Category2",
                        "r": 255,
                        "g": 170,
                        "b": 0
                    },
                    {
                        "label": "Category3",
                        "r": 169,
                        "g": 255,
                        "b": 0
                    },
                    {
                        "label": "Category4",
                        "r": 0,
                        "g": 255,
                        "b": 0
                    },
                    {
                        "label": "Category5",
                        "r": 0,
                        "g": 255,
                        "b": 170
                    },
                    {
                        "label": "Category6",
                        "r": 0,
                        "g": 169,
                        "b": 255
                    },
                    {
                        "label": "Category7",
                        "r": 0,
                        "g": 0,
                        "b": 255
                    },
                    {
                        "label": "Category8",
                        "r": 170,
                        "g": 0,
                        "b": 255
                    },
                    {
                        "label": "Category9",
                        "r": 255,
                        "g": 0,
                        "b": 169
                    }
                ]
            }
            self.save_config()
        self.open_default_dir = self.config["open_default_dir"]

        self.classes = [item['label'] for item in self.config["classes"]]
        self.classes_colors = [(item["b"], item["g"], item["r"],) for item in self.config["classes"]]

    def save_config(self):
        """保存快捷键配置到文件"""
        with open('resource/config.json', 'w') as f:
            json.dump(self.config, f, indent=4)

    def save_shortcuts(self):
        """保存快捷键配置到文件"""
        with open('resource/shortcuts.json', 'w') as f:
            json.dump(self.shortcuts, f, indent=4)

    def reload_all_setting(self):
        self._is_programmatic_change = True
        self.load_shortcuts()
        self.load_config()
        self.class_combo.clear()  # 移除所有现有选项
        self.class_combo.addItems(self.classes)  # 重新添加新的选项
        self._is_programmatic_change = False

    def open_setting(self):
        if self.setting_window is None:
            self.setting_window = MainWindow(self.reload_all_setting)
        self.setting_window.show()

    def keyPressEvent(self, event):
        """键盘事件"""
        # 获取当前按下的组合键
        modifiers = event.modifiers()
        key = event.key()

        # 构建当前按键组合字符串
        key_sequence = []
        if modifiers & Qt.ControlModifier:
            key_sequence.append("Ctrl")
        if modifiers & Qt.AltModifier:
            key_sequence.append("Alt")
        if modifiers & Qt.ShiftModifier:
            key_sequence.append("Shift")
        if modifiers & Qt.MetaModifier:
            key_sequence.append("Meta")

        # 添加主键
        key_text = self.get_key_text(key)
        if key_text and key_text not in key_sequence:  # 避免重复添加修饰键
            key_sequence.append(key_text)

        current_shortcut = "+".join(key_sequence)

        # 检查快捷键绑定并执行相应操作
        for action, shortcut in self.shortcuts.items():
            if current_shortcut == shortcut:
                if action == "open_btn":
                    self.open_image_dir()
                elif action == "prev_btn":
                    self.prev_image()
                elif action == "next_btn":
                    self.next_image()
                elif action == "save_btn":
                    self.save_labels()
                elif action == "del_btn":
                    self.delete_last_rect()
                elif action == "class_combo":
                    self.next_class()

                elif action == "setting_btn":
                    self.open_setting()
                return

        # 如果没有匹配的自定义快捷键，执行默认操作
        super().keyPressEvent(event)

    def get_class_combo_select(self):
        """返回class_combo选中的文本，颜色，序号"""
        color = self.classes_colors[self.class_combo.currentIndex()]
        bgr_color = (color[2], color[1], color[0])
        return self.class_combo.currentText(), bgr_color, self.class_combo.currentIndex()

    def get_key_text(self, key):
        """将Qt键码转换为可读字符串"""
        key_map = {
            Qt.Key_Left: "Left", Qt.Key_Right: "Right", Qt.Key_Up: "Up", Qt.Key_Down: "Down",

            Qt.Key_F1: "F1", Qt.Key_F2: "F2", Qt.Key_F3: "F3", Qt.Key_F4: "F4",
            Qt.Key_F5: "F5", Qt.Key_F6: "F6", Qt.Key_F7: "F7", Qt.Key_F8: "F8",
            Qt.Key_F9: "F9", Qt.Key_F10: "F10", Qt.Key_F11: "F11", Qt.Key_F12: "F12",

            Qt.Key_Space: "Space", Qt.Key_Enter: "Enter", Qt.Key_Return: "Enter",
            Qt.Key_Tab: "Tab", Qt.Key_Escape: "Esc", Qt.Key_Backspace: "Backspace",

            Qt.Key_Delete: "Del", Qt.Key_Insert: "Ins", Qt.Key_Home: "Home",
            Qt.Key_End: "End", Qt.Key_PageUp: "PgUp", Qt.Key_PageDown: "PgDown",

            Qt.Key_CapsLock: "CapsLock", Qt.Key_NumLock: "NumLock",
            Qt.Key_ScrollLock: "ScrollLock",
        }

        # 字母键
        if Qt.Key_A <= key <= Qt.Key_Z:
            return chr(key)
        # 数字键
        elif Qt.Key_0 <= key <= Qt.Key_9:
            return chr(key)
        # 特殊键
        elif key in key_map:
            return key_map[key]

        return None

    def save_labels(self):
        """保存标注为YOLO格式"""
        if not self.image_path or self.current_image is None:
            return

        label_path = self.get_label_path()
        img_h, img_w = self.current_image.shape[:2]

        with open(label_path, 'w') as f:
            for rect in self.rectangles:
                class_id, x1, y1, x2, y2 = rect
                x_center = ((x1 + x2) / 2) / img_w
                y_center = ((y1 + y2) / 2) / img_h
                width = (x2 - x1) / img_w
                height = (y2 - y1) / img_h
                f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
        self.statusBar().showMessage(f"标注已保存到: {label_path}")
        self.statusBar().setToolTip(f"路径: {label_path}")

    def delete_last_rect(self):
        """删除最后一个标注框"""
        if self.rectangles:
            self.rectangles.pop()
            self.show_image()
            self.statusBar().showMessage("已删除最后一个标注框")

    def prev_image(self):
        """上一张图片"""
        if hasattr(self, 'image_files') and self.current_index > 0:
            self.save_labels()
            self.current_index -= 1
            self.load_image(os.path.join(self.image_dir, self.image_files[self.current_index]))

    def next_image(self):
        """下一张图片"""
        if hasattr(self, 'image_files') and self.current_index < len(self.image_files) - 1:
            self.save_labels()
            self.current_index += 1
            self.load_image(os.path.join(self.image_dir, self.image_files[self.current_index]))

    def generate_rainbow_colors(self, n, s=1.0, l=0.5):
        colors = []
        for i in range(n):
            hue = i / n  # 色相均匀分布
            r, g, b = colorsys.hls_to_rgb(hue, l, s)  # 转换 HSL→RGB
            colors.append((int(r * 255), int(g * 255), int(b * 255)))
        return colors

    def deal_dir(self, need_deal_dir):
        self.deal_windows = ImageResizerApp(callbacks=self.open_image_dir_check_ok, deal_dir=need_deal_dir)
        self.deal_windows.show()

    def closeEvent(self, event):
        sys.exit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LabelTool()
    window.show()
    sys.exit(app.exec_())
