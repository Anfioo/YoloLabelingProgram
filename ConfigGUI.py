import sys
import json
import colorsys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QColorDialog, QGridLayout,
                             QFileDialog, QInputDialog, QScrollArea, QFrame)
from PyQt5.QtGui import QColor, QPainter, QFontMetrics, QFont, QMouseEvent
from PyQt5.QtCore import Qt, QSize, pyqtSignal

from SvgRenderer import get_config_svg_icon, set_svg_icon_from_string


class ColorLabel(QFrame):
    clicked = pyqtSignal()

    def __init__(self, index, label_data, parent=None):
        super().__init__(parent)
        self.index = index
        self.label_data = label_data
        self.selected = False

        self.setFrameShape(QFrame.Box)
        self.setLineWidth(1)
        self.setFixedSize(120, 60)  # 固定大小
        self.setCursor(Qt.PointingHandCursor)

        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 标签信息部分
        self.index_label = QLabel(f"{index}")
        self.index_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.text_label = QLabel(label_data["label"])
        self.text_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.index_label)
        layout.addWidget(self.text_label)

        self.update_color()
        self.update_selection()

    def update_color(self):
        # 设置整个标签的背景色
        color = QColor(
            self.label_data["r"],
            self.label_data["g"],
            self.label_data["b"]
        )

        # 根据背景色自动选择合适的前景色
        if (color.red() * 0.299 + color.green() * 0.587 + color.blue() * 0.114) > 150:
            text_color = Qt.black
        else:
            text_color = Qt.white

        # 应用样式
        self.setStyleSheet(f"""
            ColorLabel {{
                background-color: rgb({color.red()}, {color.green()}, {color.blue()});
                border: 1px solid gray;
            }}
            QLabel {{
                color: {'black' if text_color == Qt.black else 'white'};
            }}
        """)

    def update_selection(self):
        # 更新选中状态
        if self.selected:
            self.setStyleSheet(self.styleSheet() + "ColorLabel { border: 2px solid black; }")
        else:
            self.setStyleSheet(self.styleSheet() + "ColorLabel { border: 1px solid gray; }")

    def mousePressEvent(self, event: QMouseEvent):
        self.clicked.emit()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.clicked.emit()
        super().mouseDoubleClickEvent(event)


class JSONEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("标注编辑器")
        self.setGeometry(1000, 100, 800, 600)

        # 配置文件路径
        self.config_file = "resource/config.json"

        # 初始化数据
        self.data = {
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

        # 当前选中的标签索引
        self.current_selected = None

        # 尝试加载现有配置
        self.load_config()

        self.init_ui()
        self.update_ui()

    def init_ui(self):
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)

        # 目录选择部分
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("默认目录:"))

        self.dir_edit = QLineEdit()
        self.dir_edit.setReadOnly(True)
        dir_layout.addWidget(self.dir_edit)

        self.dir_button = QPushButton("选择目录")
        self.dir_button.clicked.connect(self.select_directory)
        dir_layout.addWidget(self.dir_button)

        main_layout.addLayout(dir_layout)

        # 类标签部分
        main_layout.addWidget(QLabel("类标签:"))

        # 创建一个可滚动的区域来放置标签
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.labels_container = QWidget()
        # 使用网格布局实现流式布局效果
        self.labels_layout = QGridLayout(self.labels_container)
        self.labels_layout.setSpacing(10)
        self.labels_layout.setContentsMargins(5, 5, 5, 5)
        self.labels_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        scroll.setWidget(self.labels_container)
        main_layout.addWidget(scroll)

        # 按钮部分
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("添加")
        self.add_button.clicked.connect(self.add_class)
        button_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("删除")
        self.remove_button.clicked.connect(self.remove_class)
        button_layout.addWidget(self.remove_button)

        self.edit_button = QPushButton("编辑")
        self.edit_button.clicked.connect(self.edit_class)
        button_layout.addWidget(self.edit_button)

        self.color_button = QPushButton("设置颜色")
        self.color_button.clicked.connect(self.set_class_color)
        button_layout.addWidget(self.color_button)

        self.format_button = QPushButton("格式化颜色")
        self.format_button.clicked.connect(self.format_colors)
        button_layout.addWidget(self.format_button)

        main_layout.addLayout(button_layout)

        set_svg_icon_from_string(self, get_config_svg_icon())
        # 存储标签对象
        self.label_widgets = {}

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_data = json.load(f)
                    # 只更新我们关心的字段
                    if "open_default_dir" in loaded_data:
                        self.data["open_default_dir"] = loaded_data["open_default_dir"]
                    if "classes" in loaded_data:
                        self.data["classes"] = loaded_data["classes"]
            except Exception as e:
                print(f"加载配置文件失败: {e}")

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def update_ui(self):
        # 更新目录显示
        self.dir_edit.setText(self.data["open_default_dir"])

        # 清除现有标签
        for i in reversed(range(self.labels_layout.count())):
            widget = self.labels_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.label_widgets.clear()

        # 计算每行可以放多少个标签 (基于窗口宽度)
        width = self.width()
        cols = max(1, width // 140)  # 每个标签大约140像素宽

        # 创建新标签
        for i, class_data in enumerate(self.data["classes"]):
            label = ColorLabel(i, class_data)
            label.clicked.connect(lambda checked=False, idx=i: self.select_label(idx))

            # 双击编辑功能
            label.mouseDoubleClickEvent = lambda event, idx=i: self.edit_class_by_index(idx)

            self.label_widgets[i] = label

            # 计算位置
            row = i // cols
            col = i % cols
            self.labels_layout.addWidget(label, row, col)

        # 保存配置
        self.save_config()

        # 如果没有选中任何标签，尝试选中第一个
        if self.current_selected is None and self.data["classes"]:
            self.select_label(0)

    def generate_rainbow_colors(self, n, s=1.0, l=0.5):
        colors = []
        for i in range(n):
            hue = i / n  # 色相均匀分布
            r, g, b = colorsys.hls_to_rgb(hue, l, s)  # 转换 HSL→RGB
            colors.append((int(r * 255), int(g * 255), int(b * 255)))
        return colors

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择默认目录", self.data["open_default_dir"])
        if directory:
            self.data["open_default_dir"] = directory
            self.update_ui()

    def select_label(self, index):
        # 取消之前选中的标签
        if self.current_selected is not None and self.current_selected in self.label_widgets:
            self.label_widgets[self.current_selected].selected = False
            self.label_widgets[self.current_selected].update_selection()

        # 选中新的标签
        if index in self.label_widgets:
            self.current_selected = index
            self.label_widgets[index].selected = True
            self.label_widgets[index].update_selection()

    def add_class(self):
        text, ok = QInputDialog.getText(self, '添加类', '输入类名:')
        if ok and text:
            # 新添加的类默认使用白色
            new_class = {"label": text, "r": 255, "g": 255, "b": 255}
            self.data["classes"].append(new_class)
            self.update_ui()
            # 选中新添加的标签
            self.select_label(len(self.data["classes"]) - 1)

    def remove_class(self):
        if self.current_selected is None:
            return

        if 0 <= self.current_selected < len(self.data["classes"]):
            del self.data["classes"][self.current_selected]
            self.current_selected = None
            self.update_ui()

    def edit_class(self):
        if self.current_selected is None:
            return

        self.edit_class_by_index(self.current_selected)

    def edit_class_by_index(self, index):
        if 0 <= index < len(self.data["classes"]):
            old_data = self.data["classes"][index]
            text, ok = QInputDialog.getText(self, '编辑类', '输入新类名(最好是英文):', text=old_data["label"])
            if ok and text and text != old_data["label"]:
                self.data["classes"][index]["label"] = text
                self.update_ui()
                # 选中编辑后的标签
                self.select_label(index)

    def set_class_color(self):
        if self.current_selected is None:
            return

        if 0 <= self.current_selected < len(self.data["classes"]):
            current_color = (
                self.data["classes"][self.current_selected]["r"],
                self.data["classes"][self.current_selected]["g"],
                self.data["classes"][self.current_selected]["b"]
            )
            color = QColorDialog.getColor(QColor(*current_color), self, "选择颜色")
            if color.isValid():
                self.data["classes"][self.current_selected]["r"] = color.red()
                self.data["classes"][self.current_selected]["g"] = color.green()
                self.data["classes"][self.current_selected]["b"] = color.blue()
                self.update_ui()
                # 保持选中状态
                self.select_label(self.current_selected)

    def format_colors(self):
        # 生成彩虹色
        colors = self.generate_rainbow_colors(len(self.data["classes"]))

        # 为每个类分配颜色
        for i, class_data in enumerate(self.data["classes"]):
            if i < len(colors):
                class_data["r"] = colors[i][0]
                class_data["g"] = colors[i][1]
                class_data["b"] = colors[i][2]

        self.update_ui()
        # 保持当前选中状态
        if self.current_selected is not None:
            self.select_label(self.current_selected)

    def resizeEvent(self, event):
        # 窗口大小改变时重新布局
        super().resizeEvent(event)
        self.update_ui()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 解决中文显示问题
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    editor = JSONEditor()
    editor.show()
    sys.exit(app.exec_())
