import sys

from PyQt5.QtWidgets import QApplication

from AutoCreateCategory import ClassMappingGenerator
from DealImagesGUI import ImageResizerApp
from FileRename import FileRenamer
from MainGUI import LabelTool
from SplitDataSets import DatasetSplitApp


def main():
    app = QApplication(sys.argv)

    # 获取命令行参数
    args = set(sys.argv[1:])  # 使用集合去重

    # 默认启动所有窗口（无参数时）
    if not args:
        args = {'--all'}

    windows = []

    # 根据参数创建对应的窗口实例
    if '--all' in args or '--class-mapping' in args:
        windows.append(ClassMappingGenerator())

    if '--all' in args or '--image-resizer' in args:
        windows.append(ImageResizerApp())

    if '--all' in args or '--file-renamer' in args:
        windows.append(FileRenamer())

    if '--all' in args or '--label-tool' in args:
        windows.append(LabelTool())

    if '--all' in args or '--dataset-split' in args:
        windows.append(DatasetSplitApp())

    # 显示所有请求的窗口
    for window in windows:
        window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
