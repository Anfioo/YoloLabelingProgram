import sys
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtCore import Qt

from SvgRenderer import get_show_svg_icon, set_svg_icon_from_string
def get_text_color(classes_background_color):
    """根据背景色决定文字颜色（黑或白）"""
    r, g, b = classes_background_color
    # 计算亮度（标准公式）
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return Qt.black if brightness > 128 else Qt.white


class ColorTextWindow(QWidget):
    def __init__(self, bg_color, classes_text, index):
        super().__init__()
        self.bg_color = bg_color
        self.text = classes_text
        self.index = index
        self.init_ui()

    def init_ui(self):
        # 设置窗口大小和标题
        self.setWindowTitle("自适应文字颜色演示")
        self.setGeometry(1000, 100, 400, 50)

        # 创建布局和标签
        layout = QVBoxLayout()
        self.label = QLabel("#" + str(self.index) + " " + self.text)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 24px; font-weight: bold;")

        # 计算文字颜色
        text_color = get_text_color(self.bg_color)

        # 设置背景色和文字颜色
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(*self.bg_color))
        palette.setColor(QPalette.WindowText, text_color)
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # 添加到布局
        layout.addWidget(self.label)
        self.setLayout(layout)
        set_svg_icon_from_string(self,get_show_svg_icon())

    def update_content(self, bg_color, classes_text, index):
        """更新背景色和文字（自动适配文字颜色）"""
        self.bg_color = bg_color
        self.text = classes_text
        self.index = index

        # 计算合适的文字颜色（黑/白）
        text_color = get_text_color(bg_color)

        # 更新标签文字
        self.label.setText("#" + str(self.index) + " " + self.text)

        # 更新背景色和文字颜色
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(*bg_color))
        palette.setColor(QPalette.WindowText, text_color)
        self.setPalette(palette)


