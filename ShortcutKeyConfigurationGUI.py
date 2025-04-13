import sys
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QLabel, QPushButton, QHBoxLayout, QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QKeySequence
from SvgRenderer import get_shortcuts_svg_icon, set_svg_icon_from_string


class ShortcutRecorder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("快捷键录制器")
        self.setGeometry(1000, 100, 500, 350)

        # 初始化按键映射
        self.init_key_map()

        # 加载配置
        self.config_file = "resource/shortcuts.json"
        self.config = self.load_config()

        # 初始化UI
        self.init_ui()

        # 当前活动的录制器
        self.active_recorder = None

    def init_key_map(self):
        """初始化按键映射表"""
        self.key_map = {
            Qt.Key_Control: "Ctrl",
            Qt.Key_Alt: "Alt",
            Qt.Key_Shift: "Shift",
            Qt.Key_Meta: "Meta",

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

        # 修饰键集合
        self.modifiers = {Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta}

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"buttonA": "Ctrl+A", "buttonB": "Ctrl+B"}

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def create_shortcut_row(self, button_name, display_name):
        """创建单个快捷键设置行"""
        group = QGroupBox(display_name)
        layout = QHBoxLayout()

        # 快捷键显示标签
        shortcut_display = QLabel(self.config.get(button_name, ""))
        shortcut_display.setAlignment(Qt.AlignCenter)
        shortcut_display.setStyleSheet("""
            QLabel {
                border: 1px solid gray;
                padding: 5px;
                background-color: white;
                min-height: 20px;
                min-width: 150px;
            }
            QLabel:hover {
                border: 1px solid black;
            }
        """)
        shortcut_display.setFont(QFont("Arial", 10))
        shortcut_display.setProperty("button_name", button_name)

        # 设置鼠标点击事件
        def start_recording(event):
            # 如果已经有活动的录制器，先停止它
            if self.active_recorder and self.active_recorder != shortcut_display:
                self.finish_recording(self.active_recorder)

            # 开始新的录制
            self.active_recorder = shortcut_display
            shortcut_display.is_recording = True
            shortcut_display.current_keys = set()
            shortcut_display.recorded_keys = []
            shortcut_display.setText("正在录制...")
            shortcut_display.setStyleSheet("""
                QLabel {
                    border: 1px solid red;
                    padding: 5px;
                    background-color: #FFF0F0;
                    min-height: 20px;
                    min-width: 150px;
                }
            """)
            self.grabKeyboard()

            # 设置定时器检查按键释放
            if not hasattr(shortcut_display, 'timer'):
                shortcut_display.timer = QTimer()
                shortcut_display.timer.timeout.connect(lambda: self.check_no_key_pressed())
            shortcut_display.timer.start(100)

        shortcut_display.mousePressEvent = start_recording

        # 清除按钮
        clear_btn = QPushButton("清除")
        clear_btn.clicked.connect(lambda: self.clear_shortcut(shortcut_display))

        layout.addWidget(shortcut_display)
        layout.addWidget(clear_btn)
        group.setLayout(layout)

        return group

    def init_ui(self):

        central_widget = QWidget()
        layout = QVBoxLayout()

        # 添加快捷键设置行
        self.button_a_group = self.create_shortcut_row("open_btn", "打开图片文件夹快捷键")
        self.button_b_group = self.create_shortcut_row("prev_btn", "上一张快捷键")
        self.button_c_group = self.create_shortcut_row("next_btn", "下一张快捷键")
        self.button_d_group = self.create_shortcut_row("class_combo", "类别快捷键")
        self.button_e_group = self.create_shortcut_row("save_btn", "保存快捷键")
        self.button_f_group = self.create_shortcut_row("del_btn", "删除快捷键")
        self.button_g_group = self.create_shortcut_row("setting_btn", "设置快捷键")

        layout.addWidget(self.button_a_group)
        layout.addWidget(self.button_b_group)
        layout.addWidget(self.button_c_group)
        layout.addWidget(self.button_d_group)
        layout.addWidget(self.button_e_group)
        layout.addWidget(self.button_f_group)
        layout.addWidget(self.button_g_group)

        # 保存按钮
        save_btn = QPushButton("保存所有快捷键")
        save_btn.clicked.connect(self.save_config)
        layout.addWidget(save_btn)

        # 提示信息
        hint_label = QLabel("提示：点击快捷键区域开始录制，最多支持3个键的组合")
        hint_label.setStyleSheet("color: green; font-size: 10px;")
        layout.addWidget(hint_label)

        supported_keys_label = QLabel("支持的特殊按键: 方向键(↑↓←→), 特殊字符([]();),功能键(F1-F12), 空格, Enter等")
        supported_keys_label.setStyleSheet("color: green; font-size: 10px;")
        supported_keys_label.setWordWrap(True)
        layout.addWidget(supported_keys_label)

        central_widget.setLayout(layout)
        set_svg_icon_from_string(self,get_shortcuts_svg_icon())

        self.setCentralWidget(central_widget)

    def check_no_key_pressed(self):
        if self.active_recorder and hasattr(self.active_recorder, 'current_keys'):
            if not self.active_recorder.current_keys and hasattr(self.active_recorder,
                                                                 'recorded_keys') and self.active_recorder.recorded_keys:
                self.finish_recording(self.active_recorder)

    def finish_recording(self, shortcut_display):
        if not shortcut_display:
            return

        if hasattr(shortcut_display, 'is_recording') and shortcut_display.is_recording:
            shortcut_display.is_recording = False
            if hasattr(shortcut_display, 'timer'):
                shortcut_display.timer.stop()

            self.releaseKeyboard()

            # 保存录制的快捷键
            if hasattr(shortcut_display, 'recorded_keys') and shortcut_display.recorded_keys:
                formatted = "+".join(shortcut_display.recorded_keys)
                shortcut_display.setText(formatted)
                button_name = shortcut_display.property("button_name")
                if button_name:
                    self.config[button_name] = formatted
            else:
                shortcut_display.setText("")
                button_name = shortcut_display.property("button_name")
                if button_name:
                    self.config[button_name] = ""

            # 恢复样式
            shortcut_display.setStyleSheet("""
                QLabel {
                    border: 1px solid gray;
                    padding: 5px;
                    background-color: white;
                    min-height: 20px;
                    min-width: 150px;
                }
                QLabel:hover {
                    border: 1px solid black;
                }
            """)

            if self.active_recorder == shortcut_display:
                self.active_recorder = None

    def clear_shortcut(self, shortcut_display):
        shortcut_display.setText("")
        button_name = shortcut_display.property("button_name")
        if button_name:
            self.config[button_name] = ""

    def keyPressEvent(self, event):
        if not self.active_recorder:
            return

        key = event.key()

        # 忽略重复按键
        if event.isAutoRepeat():
            return

        # 转换按键为可读字符串
        key_text = self.get_key_text(key)

        if key_text and key not in getattr(self.active_recorder, 'current_keys', set()):
            if not hasattr(self.active_recorder, 'current_keys'):
                self.active_recorder.current_keys = set()
            self.active_recorder.current_keys.add(key)

            # 添加到录制列表（最多3个）
            if not hasattr(self.active_recorder, 'recorded_keys'):
                self.active_recorder.recorded_keys = []

            if len(self.active_recorder.recorded_keys) < 3:
                # 分离修饰键和普通键
                modifiers = []
                normal_keys = []

                for k in self.active_recorder.current_keys:
                    text = self.get_key_text(k)
                    if k in self.modifiers:
                        modifiers.append(text)
                    else:
                        normal_keys.append(text)

                # 排序修饰键：Ctrl > Alt > Shift > Meta
                modifier_order = ["Ctrl", "Alt", "Shift", "Meta"]
                sorted_modifiers = [m for m in modifier_order if m in modifiers]

                # 合并并限制最大3个键
                combined = sorted_modifiers + normal_keys
                if len(combined) > 3:
                    combined = combined[:3]

                self.active_recorder.recorded_keys = combined

            # 更新显示
            display_text = "+".join(self.active_recorder.recorded_keys)
            self.active_recorder.setText(display_text)

            # 如果已经达到3个键，停止录制
            if len(self.active_recorder.recorded_keys) >= 3:
                self.finish_recording(self.active_recorder)

    def keyReleaseEvent(self, event):
        if not self.active_recorder:
            return

        key = event.key()

        # 忽略重复按键
        if event.isAutoRepeat():
            return

        if hasattr(self.active_recorder, 'current_keys') and key in self.active_recorder.current_keys:
            self.active_recorder.current_keys.remove(key)

    def get_key_text(self, key):
        # 首先检查自定义映射
        if key in self.key_map:
            return self.key_map[key]

        # 处理字母和数字键
        if Qt.Key_A <= key <= Qt.Key_Z:
            return chr(key)
        elif Qt.Key_0 <= key <= Qt.Key_9:
            return chr(key)
        elif Qt.Key_F1 <= key <= Qt.Key_F24:
            return f"F{key - Qt.Key_F1 + 1}"

        # 尝试使用QKeySequence获取按键名称
        key_str = QKeySequence(key).toString()
        if key_str and len(key_str) == 1 and key_str.isprintable():
            return key_str

        return None

    def closeEvent(self, event):
        self.save_config()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ShortcutRecorder()
    window.show()
    sys.exit(app.exec_())
