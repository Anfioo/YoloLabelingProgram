import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QTextEdit,
                             QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
from SvgRenderer import get_category_svg_icon, set_svg_icon_from_string


class ClassMappingGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('类别映射生成器')
        self.setGeometry(300, 300, 800, 600)

        # 主窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 布局
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # 文件选择部分
        self.file_group = QWidget()
        self.file_layout = QVBoxLayout()
        self.file_group.setLayout(self.file_layout)

        self.source_file_layout = QHBoxLayout()
        self.source_label = QLabel('源映射文件: 未选择')
        self.select_source_btn = QPushButton('选择源文件')
        self.select_source_btn.clicked.connect(self.select_source_file)

        self.source_file_layout.addWidget(self.source_label)
        self.source_file_layout.addWidget(self.select_source_btn)
        self.file_layout.addLayout(self.source_file_layout)

        # 配置文件路径显示
        self.config_path = os.path.join("resource", "config.json")
        self.config_label = QLabel(f'目标配置文件: {self.config_path}')
        self.file_layout.addWidget(self.config_label)

        self.main_layout.addWidget(self.file_group)

        # 结果显示部分
        self.result_group = QWidget()
        self.result_layout = QVBoxLayout()
        self.result_group.setLayout(self.result_layout)

        self.result_label = QLabel('生成的映射:')
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)

        self.result_layout.addWidget(self.result_label)
        self.result_layout.addWidget(self.result_text)
        self.main_layout.addWidget(self.result_group)

        # 按钮部分
        self.btn_group = QWidget()
        self.btn_layout = QHBoxLayout()
        self.btn_group.setLayout(self.btn_layout)

        self.generate_btn = QPushButton('生成映射')
        self.generate_btn.clicked.connect(self.generate_mapping)

        self.replace_btn = QPushButton('替换配置文件')
        self.replace_btn.clicked.connect(self.replace_config)
        self.replace_btn.setEnabled(False)

        self.btn_layout.addWidget(self.generate_btn)
        self.btn_layout.addWidget(self.replace_btn)
        self.main_layout.addWidget(self.btn_group)

        # 状态栏
        self.statusBar().showMessage('准备就绪')

        # 初始化变量
        self.selected_source_file = None
        self.generated_mapping = None

        set_svg_icon_from_string(self,get_category_svg_icon())

    def select_source_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "选择源映射文件", "",
            "文本文件 (*.txt);;所有文件 (*)", options=options)

        if file_name:
            self.selected_source_file = file_name
            self.source_label.setText(f'源映射文件: {file_name}')
            self.statusBar().showMessage('源文件已选择')

    def generate_mapping(self):
        if not self.selected_source_file:
            QMessageBox.warning(self, '警告', '请先选择源文件!')
            return

        try:
            self.generated_mapping = self.generate_class_mapping(self.selected_source_file).get("classes")
            self.result_text.setPlainText(json.dumps(self.generated_mapping, indent=4, ensure_ascii=False))
            self.replace_btn.setEnabled(True)
            self.statusBar().showMessage('映射生成成功')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'生成映射时出错:\n{str(e)}')
            self.statusBar().showMessage('生成映射失败')

    def replace_config(self):
        if not self.generated_mapping:
            QMessageBox.warning(self, '警告', '请先生成映射!')
            return

        try:
            # 确保resource目录存在
            os.makedirs("resource", exist_ok=True)

            # 读取或创建config.json
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}

            # 更新classes部分
            config["classes"] = self.generated_mapping

            # 写入文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            QMessageBox.information(self, '成功', '配置文件已更新!')
            self.statusBar().showMessage('配置文件更新成功')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'更新配置文件时出错:\n{str(e)}')
            self.statusBar().showMessage('配置文件更新失败')

    def generate_class_mapping(self, file_path):
        """
        从class_mapping.txt文件中读取class_to_id映射，并生成对应的classes列表

        参数:
            file_path (str): class_mapping.txt文件路径

        返回:
            dict: 包含class_to_id和classes的字典
        """
        # 读取class_mapping.txt文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 获取class_to_id映射
        class_to_id = data.get("class_to_id", {})

        # 生成classes列表
        classes = []
        for class_name in class_to_id.keys():
            class_info = {
                "label": class_name,
                "r": 0,
                "g": 0,
                "b": 0
            }
            classes.append(class_info)

        # 返回完整映射
        return {
            "classes": classes
        }


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ClassMappingGenerator()
    window.show()
    sys.exit(app.exec_())
