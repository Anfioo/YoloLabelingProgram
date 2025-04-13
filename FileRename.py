import os
import shutil
import json

from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QLineEdit, QFileDialog,
                             QRadioButton, QButtonGroup, QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QUrl

from SvgRenderer import get_re_filename_svg_icon, set_svg_icon_from_string

class FileRenamer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('文件重命名工具')
        self.setGeometry(300, 300, 500, 300)

        # 主布局
        layout = QVBoxLayout()

        # 源文件夹选择
        source_layout = QHBoxLayout()
        source_label = QLabel('源文件夹:')
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText('请选择源文件夹路径')
        source_btn = QPushButton('浏览...')
        source_btn.clicked.connect(self.browseSource)
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.source_edit)
        source_layout.addWidget(source_btn)

        # 目标文件夹选择
        target_layout = QHBoxLayout()
        target_label = QLabel('目标文件夹:')
        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText('自动生成在源文件夹同级目录')
        target_btn = QPushButton('浏览...')
        target_btn.clicked.connect(self.browseTarget)
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.target_edit)
        target_layout.addWidget(target_btn)

        # 重命名选项
        options_layout = QVBoxLayout()
        options_label = QLabel('重命名选项:')
        self.prefix_radio = QRadioButton('前缀模式 (文件夹_序号)')
        self.suffix_radio = QRadioButton('后缀模式 (序号_文件夹)')
        self.prefix_radio.setChecked(True)

        self.rename_group = QButtonGroup()
        self.rename_group.addButton(self.prefix_radio)
        self.rename_group.addButton(self.suffix_radio)

        options_layout.addWidget(options_label)
        options_layout.addWidget(self.prefix_radio)
        options_layout.addWidget(self.suffix_radio)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        # 执行按钮
        execute_btn = QPushButton('开始重命名')
        execute_btn.clicked.connect(self.executeRename)

        # 添加到主布局
        layout.addLayout(source_layout)
        layout.addLayout(target_layout)
        layout.addLayout(options_layout)
        layout.addWidget(self.progress)
        layout.addWidget(execute_btn)

        self.setLayout(layout)
        set_svg_icon_from_string(self,get_re_filename_svg_icon())

    def browseSource(self):
        folder = QFileDialog.getExistingDirectory(self, '选择源文件夹')
        if folder:
            self.source_edit.setText(folder)
            # 自动设置目标文件夹
            parent_dir = os.path.dirname(folder)
            folder_name = os.path.basename(folder)
            target_dir = os.path.join(parent_dir, f"{folder_name}_ok")
            self.target_edit.setText(target_dir)

    def browseTarget(self):
        folder = QFileDialog.getExistingDirectory(self, '选择目标文件夹')
        if folder:
            self.target_edit.setText(folder)

    def executeRename(self):
        source_dir = self.source_edit.text()
        target_dir = self.target_edit.text()

        if not source_dir:
            QMessageBox.warning(self, '警告', '请选择源文件夹')
            return

        if not os.path.exists(source_dir):
            QMessageBox.warning(self, '警告', '源文件夹不存在')
            return

        if not target_dir:
            parent_dir = os.path.dirname(source_dir)
            folder_name = os.path.basename(source_dir)
            target_dir = os.path.join(parent_dir, f"{folder_name}_ok")
            self.target_edit.setText(target_dir)

        # 收集所有文件并按文件夹分组
        folder_files = {}
        for root, dirs, files in os.walk(source_dir):
            # 获取相对于源文件夹的路径
            rel_path = os.path.relpath(root, source_dir)

            # 如果是源文件夹本身，使用源文件夹名
            if rel_path == '.':
                folder_name = os.path.basename(root)
            else:
                # 获取直接父文件夹名
                folder_name = os.path.basename(root)

            # 确保每个文件夹有自己的文件列表
            if folder_name not in folder_files:
                folder_files[folder_name] = []

            for file in files:
                file_path = os.path.join(root, file)
                folder_files[folder_name].append((file_path, file))

        # 如果没有文件，直接返回
        if not folder_files:
            QMessageBox.information(self, '信息', '没有找到可重命名的文件')
            return

        # 按文件夹名排序
        sorted_folders = sorted(folder_files.keys())

        # 创建目标文件夹
        os.makedirs(target_dir, exist_ok=True)

        # 计算总文件数用于进度条
        total_files = sum(len(files) for files in folder_files.values())
        self.progress.setRange(0, total_files)

        current_count = 0
        file_counter = 1  # 从1开始计数

        # 确定序号位数
        num_digits = len(str(total_files))

        # 创建类别映射字典
        class_mapping = {}
        # 为每个文件夹分配一个ID（按字母顺序）
        class_ids = {folder: idx for idx, folder in enumerate(sorted(sorted_folders))}

        # 创建结果字典，保存文件名到类别ID的映射
        result_mapping = {}

        # 遍历每个文件夹
        for folder_name in sorted_folders:
            files = folder_files[folder_name]

            # 遍历文件夹中的每个文件
            for file_path, orig_name in files:
                ext = os.path.splitext(orig_name)[1]

                if self.prefix_radio.isChecked():
                    new_name = f"{folder_name}_{str(file_counter).zfill(num_digits)}{ext}"
                else:
                    new_name = f"{str(file_counter).zfill(num_digits)}_{folder_name}{ext}"

                dst_path = os.path.join(target_dir, new_name)

                try:
                    shutil.copy2(file_path, dst_path)
                    # 添加到结果映射
                    result_mapping[new_name] = class_ids[folder_name]
                except Exception as e:
                    QMessageBox.warning(self, '错误', f'复制文件失败: {str(e)}')
                    return

                current_count += 1
                file_counter += 1
                self.progress.setValue(current_count)
                QApplication.processEvents()  # 更新UI

        # 保存映射到JSON文件
        path_dirname = os.path.dirname(target_dir)
        mapping_file = os.path.join(path_dirname, "class_mapping.txt")
        with open(mapping_file, 'w') as f:
            json.dump({
                'class_to_id': class_ids,
                'file_to_class': result_mapping
            }, f, indent=4)

        QMessageBox.information(self, '完成',
                                f'成功重命名并复制了 {current_count} 个文件\n'
                                f'类别映射已保存到 {mapping_file}')

        url1 = QUrl.fromLocalFile(path_dirname)
        url2 = QUrl.fromLocalFile(mapping_file)
        QDesktopServices.openUrl(url1)
        QDesktopServices.openUrl(url2)


if __name__ == '__main__':
    app = QApplication([])
    window = FileRenamer()
    window.show()
    app.exec_()
