import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget

from ConfigGUI import JSONEditor
from AutoCreateCategory import ClassMappingGenerator
from ShortcutKeyConfigurationGUI import ShortcutRecorder

from SvgRenderer import get_setting_svg_icon, set_svg_icon_from_string
from IntroduceGUI import ProfileWindow

class MainWindow(QMainWindow):
    def __init__(self, reload_callback=None):
        super().__init__()

        self.setWindowTitle("设置")
        self.setGeometry(700, 400, 300, 200)
        self.reload_callback = reload_callback

        self.ShortcutRecorder = None
        self.ConfigGUI = None
        self.Introduce = None
        self.Labels = None
        # 创建主部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # 创建按钮1
        self.button_a = QPushButton("快捷键设置")
        self.button_a.clicked.connect(self.shortcut_keys_setting)
        layout.addWidget(self.button_a)

        # 创建按钮2
        self.button_b = QPushButton("标注设置")
        self.button_b.clicked.connect(self.annotation_setting)
        layout.addWidget(self.button_b)

        # 创建按钮4
        self.button_d = QPushButton("自动标注配置")
        self.button_d.clicked.connect(self.annotation_labels)
        layout.addWidget(self.button_d)

        # 创建按钮3
        self.button_c = QPushButton("关于")
        self.button_c.clicked.connect(self.annotation_introduce)
        layout.addWidget(self.button_c)


        # 设置布局
        central_widget.setLayout(layout)
        set_svg_icon_from_string(self, get_setting_svg_icon())

    def shortcut_keys_setting(self):
        if self.ShortcutRecorder is None:
            self.ShortcutRecorder = ShortcutRecorder()
        self.ShortcutRecorder.show()

    def annotation_setting(self):
        if self.ConfigGUI is None:
            self.ConfigGUI = JSONEditor()
        self.ConfigGUI.show()



    def annotation_introduce(self):
        if self.Introduce is None:
            self.Introduce = ProfileWindow()
        self.Introduce.show()

    def annotation_labels(self):
        if self.Labels is None:
            self.Labels = ClassMappingGenerator()
        self.Labels.show()


    def closeEvent(self, event):
        # 如果提供了回调函数，则调用
        if self.reload_callback:
            self.reload_callback()

        super().closeEvent(event)  # 确保父类的关闭逻辑执行


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
