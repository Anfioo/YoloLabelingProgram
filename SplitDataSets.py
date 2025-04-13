import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox,
                             QGroupBox, QDoubleSpinBox, QTextEdit, QScrollArea)
from PyQt5.QtCore import Qt, QObject, pyqtSignal

import os
import random
import shutil
import json
import yaml
from pathlib import Path
from tqdm import tqdm
import io
import contextlib

from SvgRenderer import get_split_svg_icon, set_svg_icon_from_string


class EmittingStream(QObject):
    textWritten = pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))

    def flush(self):
        pass


class DatasetSplitApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("数据集分割工具")
        self.setGeometry(100, 100, 800, 600)  # 增大窗口尺寸以容纳输出区域

        # 创建自定义流并连接信号
        self.stdout_stream = EmittingStream()
        self.stdout_stream.textWritten.connect(self.normal_output_written)

        self.init_ui()

    def normal_output_written(self, text):
        """将文本追加到输出区域"""
        cursor = self.output_text.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(text)
        self.output_text.ensureCursorVisible()

    def init_ui(self):
        # 主窗口部件
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # 创建输入组
        input_group = QGroupBox("数据集配置")
        input_layout = QVBoxLayout()

        # 图像目录
        self.images_dir_label = QLabel("图像目录:")
        self.images_dir_edit = QLineEdit()
        self.images_dir_btn = QPushButton("浏览...")
        self.images_dir_btn.clicked.connect(lambda: self.browse_directory(self.images_dir_edit))
        images_dir_layout = QHBoxLayout()
        images_dir_layout.addWidget(self.images_dir_label)
        images_dir_layout.addWidget(self.images_dir_edit)
        images_dir_layout.addWidget(self.images_dir_btn)

        # 标签目录
        self.labels_dir_label = QLabel("标签目录:")
        self.labels_dir_edit = QLineEdit()
        self.labels_dir_btn = QPushButton("浏览...")
        self.labels_dir_btn.clicked.connect(lambda: self.browse_directory(self.labels_dir_edit))
        labels_dir_layout = QHBoxLayout()
        labels_dir_layout.addWidget(self.labels_dir_label)
        labels_dir_layout.addWidget(self.labels_dir_edit)
        labels_dir_layout.addWidget(self.labels_dir_btn)

        # 输出目录
        self.output_dir_label = QLabel("输出目录:")
        self.output_dir_edit = QLineEdit()
        self.output_dir_btn = QPushButton("浏览...")
        self.output_dir_btn.clicked.connect(lambda: self.browse_directory(self.output_dir_edit))
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_label)
        output_dir_layout.addWidget(self.output_dir_edit)
        output_dir_layout.addWidget(self.output_dir_btn)

        # 类别映射文件
        self.class_mapping_label = QLabel("类别映射文件:")
        self.class_mapping_edit = QLineEdit()
        self.class_mapping_btn = QPushButton("浏览...")
        self.class_mapping_btn.clicked.connect(lambda: self.browse_file(self.class_mapping_edit))
        class_mapping_layout = QHBoxLayout()
        class_mapping_layout.addWidget(self.class_mapping_label)
        class_mapping_layout.addWidget(self.class_mapping_edit)
        class_mapping_layout.addWidget(self.class_mapping_btn)

        # 验证集比例
        self.val_ratio_label = QLabel("验证集比例:")
        self.val_ratio_spin = QDoubleSpinBox()
        self.val_ratio_spin.setRange(0.01, 0.99)
        self.val_ratio_spin.setSingleStep(0.05)
        self.val_ratio_spin.setValue(0.2)
        val_ratio_layout = QHBoxLayout()
        val_ratio_layout.addWidget(self.val_ratio_label)
        val_ratio_layout.addWidget(self.val_ratio_spin)
        val_ratio_layout.addStretch()

        # 添加到输入组
        input_layout.addLayout(images_dir_layout)
        input_layout.addLayout(labels_dir_layout)
        input_layout.addLayout(output_dir_layout)
        input_layout.addLayout(class_mapping_layout)
        input_layout.addLayout(val_ratio_layout)
        input_group.setLayout(input_layout)

        # 创建按钮组
        btn_group = QWidget()
        btn_layout = QHBoxLayout()

        self.run_btn = QPushButton("开始分割")
        self.run_btn.clicked.connect(self.run_split)
        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self.clear_fields)
        self.clear_output_btn = QPushButton("清空输出")
        self.clear_output_btn.clicked.connect(self.clear_output)

        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.clear_output_btn)
        btn_group.setLayout(btn_layout)

        # 创建输出区域
        output_group = QGroupBox("输出信息")
        output_layout = QVBoxLayout()

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setLineWrapMode(QTextEdit.NoWrap)
        self.output_text.setStyleSheet("font-family: Courier; font-size: 10pt;")

        # 添加滚动区域
        scroll = QScrollArea()
        scroll.setWidget(self.output_text)
        scroll.setWidgetResizable(True)
        output_layout.addWidget(scroll)
        output_group.setLayout(output_layout)

        # 添加到主布局
        main_layout.addWidget(input_group)
        main_layout.addWidget(btn_group)
        main_layout.addWidget(output_group)
        main_widget.setLayout(main_layout)

        self.setCentralWidget(main_widget)

        # 设置默认值（可选）
        self.set_default_values()
        set_svg_icon_from_string(self, get_split_svg_icon())

    def set_default_values(self):
        """设置默认值，方便测试"""
        self.images_dir_edit.setText(r"images")
        self.labels_dir_edit.setText(r"labels")
        self.output_dir_edit.setText("datasets")
        self.class_mapping_edit.setText(r"class_mapping.txt")

    def browse_directory(self, line_edit):
        """浏览目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择目录")
        if dir_path:
            line_edit.setText(dir_path)

    def browse_file(self, line_edit):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if file_path:
            line_edit.setText(file_path)

    def clear_fields(self):
        """清空所有输入字段"""
        self.images_dir_edit.clear()
        self.labels_dir_edit.clear()
        self.output_dir_edit.clear()
        self.class_mapping_edit.clear()
        self.val_ratio_spin.setValue(0.2)

    def clear_output(self):
        """清空输出区域"""
        self.output_text.clear()

    def validate_inputs(self):
        """验证输入是否有效"""
        if not all([
            self.images_dir_edit.text(),
            self.labels_dir_edit.text(),
            self.output_dir_edit.text(),
            self.class_mapping_edit.text()
        ]):
            QMessageBox.warning(self, "警告", "所有字段都必须填写！")
            return False

        if not os.path.isdir(self.images_dir_edit.text()):
            QMessageBox.warning(self, "警告", "图像目录不存在！")
            return False

        if not os.path.isdir(self.labels_dir_edit.text()):
            QMessageBox.warning(self, "警告", "标签目录不存在！")
            return False

        if not os.path.isfile(self.class_mapping_edit.text()):
            QMessageBox.warning(self, "警告", "类别映射文件不存在！")
            return False

        return True

    def run_split(self):
        """执行数据集分割"""
        if not self.validate_inputs():
            return

        try:
            # 重定向标准输出到我们的自定义流
            old_stdout = sys.stdout
            sys.stdout = self.stdout_stream

            # 使用contextlib来捕获tqdm的输出
            output_buffer = io.StringIO()
            with contextlib.redirect_stdout(output_buffer):
                create_dataset_split(
                    images_dir=self.images_dir_edit.text(),
                    labels_dir=self.labels_dir_edit.text(),
                    output_dir=self.output_dir_edit.text(),
                    val_ratio=self.val_ratio_spin.value(),
                    class_mapping_file=self.class_mapping_edit.text()
                )

                # 将缓冲区的输出发送到UI
                self.stdout_stream.write(output_buffer.getvalue())

            QMessageBox.information(self, "成功", "数据集分割完成！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"分割过程中出错:\n{str(e)}")
            self.stdout_stream.write(f"\n错误: {str(e)}\n")
        finally:
            # 恢复标准输出
            sys.stdout = old_stdout


def create_dataset_split(
        images_dir="images",
        labels_dir="labels",
        output_dir="datasets",
        val_ratio=0.2,
        seed=42,
        class_mapping_file="class_mapping.json"
):
    """
    自动创建训练集/验证集分割

    参数:
        images_dir: 原始图片目录
        labels_dir: 原始标签目录
        output_dir: 输出目录
        val_ratio: 验证集比例(0-1)
        seed: 随机种子
        class_mapping_file: 包含类别映射的JSON文件路径
    """
    # 读取类别映射文件
    with open(class_mapping_file) as f:
        class_mapping = json.load(f)

    class_to_id = class_mapping["class_to_id"]
    id_to_class = {v: k for k, v in class_to_id.items()}

    # 按ID排序获取标准类别顺序
    CLASS_ORDER = [id_to_class[i] for i in sorted(id_to_class.keys())]

    # 创建输出目录结构
    (Path(output_dir) / "images/train").mkdir(parents=True, exist_ok=True)
    (Path(output_dir) / "images/val").mkdir(parents=True, exist_ok=True)
    (Path(output_dir) / "labels/train").mkdir(parents=True, exist_ok=True)
    (Path(output_dir) / "labels/val").mkdir(parents=True, exist_ok=True)

    # 获取所有图片并按类别分组
    print("🔍 扫描图片文件中...")
    class_files = {}
    for img_file in tqdm(os.listdir(images_dir), desc="处理图片"):
        if not img_file.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue

        # 从文件名提取类别 (支持 Anger_001.png 和 001_Anger.png 格式)
        parts = os.path.splitext(img_file)[0].split('_')
        if parts[0].isdigit():
            class_name = parts[1]
        else:
            class_name = parts[0]

        if class_name not in class_to_id:
            raise ValueError(f"发现未定义的类别: {class_name} (来自文件: {img_file})")

        if class_name not in class_files:
            class_files[class_name] = []
        class_files[class_name].append(img_file)

    # 验证所有找到的类别都在映射文件中
    for class_name in class_files.keys():
        if class_name not in class_to_id:
            raise ValueError(f"发现未定义的类别: {class_name}")

    # 按标准顺序重新组织类别
    ordered_classes = [c for c in CLASS_ORDER if c in class_files]
    class_stats = {c: 0 for c in ordered_classes}

    print("\n📊 开始分割数据集...")
    random.seed(seed)
    for class_name in tqdm(ordered_classes, desc="处理类别"):
        files = class_files[class_name]
        random.shuffle(files)

        # 计算验证集数量 (至少保留1张)
        val_count = max(1, int(len(files) * val_ratio))
        val_files = files[:val_count]
        train_files = files[val_count:]

        class_stats[class_name] = {
            'train': len(train_files),
            'val': len(val_files),
            'total': len(files)
        }

        # 使用进度条复制文件
        for phase, files in [('train', train_files), ('val', val_files)]:
            for img_file in tqdm(files, desc=f"复制 {class_name} {phase} 文件", leave=False):
                # 处理图片文件
                img_path = os.path.join(images_dir, img_file)
                shutil.copy(img_path, f"{output_dir}/images/{phase}/{img_file}")

                # 处理对应的标签文件
                label_file = os.path.splitext(img_file)[0] + '.txt'
                label_path = os.path.join(labels_dir, label_file)
                if os.path.exists(label_path):
                    shutil.copy(label_path, f"{output_dir}/labels/{phase}/{label_file}")

    # 创建标准格式的YAML配置文件
    yaml_content = {
        'path': str(Path(output_dir).resolve()),
        'train': 'images/train',
        'val': 'images/val',
        'nc': len(ordered_classes),
        'names': CLASS_ORDER
    }

    yaml_path = Path(output_dir) / "dataset.yaml"
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_content, f, sort_keys=False, default_flow_style=None)

    # 打印统计信息
    print("\n✅ 数据集分割完成")
    print(f"📁 输出目录: {output_dir}")
    print(f"🎯 类别数量: {len(ordered_classes)}")
    print("\n📊 各类别数量统计:")
    max_name_len = max(len(c) for c in ordered_classes)
    for class_name in ordered_classes:
        stats = class_stats[class_name]
        print(f"  {class_name.ljust(max_name_len)} : "
              f"训练集={str(stats['train']).rjust(4)} "
              f"验证集={str(stats['val']).rjust(4)} "
              f"总计={str(stats['total']).rjust(4)}")

    print(f"\n📄 YAML配置文件已生成: {yaml_path}")
    print("🎯 标准格式预览:")
    print("=" * 40)
    with open(yaml_path) as f:
        print(f.read())
    print("=" * 40)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DatasetSplitApp()
    window.show()
    sys.exit(app.exec_())
