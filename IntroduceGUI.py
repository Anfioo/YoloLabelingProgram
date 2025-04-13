import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTextBrowser, QFrame, QDialog)
from PyQt5.QtGui import QPixmap, QIcon, QFont, QTextCursor
from PyQt5.QtCore import Qt, QSize, QMargins
from SvgRenderer import get_introduce_svg_icon, set_svg_icon_from_string


class ProfileWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 窗口设置
        self.setWindowTitle('✨ Anfioo 个人简介 ✨')
        self.setWindowIcon(QIcon('assets/avatar.png'))
        self.setFixedSize(600, 700)  # 调整窗口大小
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f7fa;
                color: #333;
            }
        """)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(40, 40, 40, 40)

        # 头像部分
        avatar_frame = QFrame()
        avatar_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 100px;
                border: 5px solid #e0e6ff;
            }
        """)
        avatar_frame.setFixedSize(150, 150)

        avatar_layout = QVBoxLayout(avatar_frame)
        avatar_layout.setContentsMargins(0, 0, 0, 0)

        avatar_label = QLabel()
        pixmap = QPixmap('assets/avatar.png')
        avatar_label.setPixmap(pixmap.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        avatar_label.setAlignment(Qt.AlignCenter)
        avatar_layout.addWidget(avatar_label)

        # 名字/标题
        name_label = QLabel("Anfioo")
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #3a4a6b;
                margin-top: 10px;
            }
        """)

        # 简介 - 使用富文本美化
        bio_text = """
        <div style='text-align: center; font-size: 15px;'>
            <p style='color: #5a6da7; margin: 8px 0;'>😊 你好！我是Anfioo，一名开发者/创作者 😊</p>
            <p style='color: #6a7db8; margin: 8px 0;'>🌟 热爱编程、开源和技术分享 🌟</p>
            <p style='color: #7a8dc9; margin: 8px 0;'>💡 软件不足之处可以去B站上评论 💡</p>
            <p style='color: #8a9dda; margin: 8px 0;'>🎉 欢迎访问我的GitHub和哔哩哔哩主页 🎉</p>
        </div>
        """
        bio_label = QLabel(bio_text)
        bio_label.setAlignment(Qt.AlignCenter)
        bio_label.setWordWrap(True)
        bio_label.setStyleSheet("background-color: white; border-radius: 15px; padding: 15px;")

        # 链接按钮
        github_btn = self.create_link_button(
            "GitHub",
            "https://github.com/Anfioo",
            "assets/github.png",
            "#24292e"
        )

        bilibili_btn = self.create_link_button(
            "哔哩哔哩",
            "https://space.bilibili.com/1821689715",
            "assets/bilibili.png",
            "#fb7299"
        )

        # 按钮布局
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        btn_layout.addWidget(github_btn)
        btn_layout.addSpacing(20)
        btn_layout.addWidget(bilibili_btn)
        btn_layout.addStretch(1)

        # 许可证按钮
        license_btn = QPushButton("📜 查看许可证 (GPL-3.0)")
        license_btn.setCursor(Qt.PointingHandCursor)
        license_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 25px;
                font-size: 15px;
                font-weight: bold;
                border-radius: 8px;
                background-color: #e0e6ff;
                color: #3a4a6b;
                border: 2px solid #b8c5ff;
            }
            QPushButton:hover {
                background-color: #b8c5ff;
            }
        """)
        license_btn.clicked.connect(self.show_license)

        # 添加到主布局
        main_layout.addWidget(avatar_frame, 0, Qt.AlignCenter)
        main_layout.addWidget(name_label)
        main_layout.addWidget(bio_label)
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(license_btn, 0, Qt.AlignCenter)
        main_layout.addStretch(1)

        self.setLayout(main_layout)
        set_svg_icon_from_string(self, get_introduce_svg_icon())

    def create_link_button(self, text, url, icon_path=None, color="#3a4a6b"):
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                padding: 12px 25px;
                font-size: 15px;
                font-weight: bold;
                border-radius: 8px;
                background-color: white;
                color: {color};
                border: 2px solid #d9e0ff;
            }}
            QPushButton:hover {{
                background-color: #f0f4ff;
            }}
        """)

        if icon_path:
            try:
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(24, 24))
            except:
                pass

        btn.clicked.connect(lambda: self.open_link(url))
        return btn

    def open_link(self, url):
        import webbrowser
        webbrowser.open(url)

    def show_license(self):
        license_dialog = QDialog(self)
        license_dialog.setWindowTitle("📄 GNU GPL-3.0 许可证")
        license_dialog.setModal(True)
        license_dialog.setFixedSize(550, 600)
        license_dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QTextBrowser {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
                font-family: "Microsoft YaHei", sans-serif;
                font-size: 13px;
                border: 1px solid #e0e6ff;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f4ff;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #c1d0ff;
                min-height: 20px;
                border-radius: 5px;
            }
        """)

        layout = QVBoxLayout(license_dialog)
        layout.setContentsMargins(20, 20, 20, 20)

        license_browser = QTextBrowser()
        license_browser.setOpenExternalLinks(True)

        license_html = """
        <div style='font-family: "Microsoft YaHei", sans-serif;'>
            <h2 style='color: #3a4a6b; text-align: center;'>GNU GENERAL PUBLIC LICENSE</h2>
            <h3 style='color: #5a6da7; text-align: center;'>Version 3, 29 June 2007</h3>
            
            <div style='background-color: #f0f4ff; padding: 15px; border-radius: 8px; margin: 15px 0;'>
                <h4 style='color: #3a4a6b; margin-top: 0;'>Anfioo's Personal Profile Viewer</h4>
                <p style='color: #5a6da7;'>Copyright (C) 2023 Anfioo</p>
                
                <p style='color: #6a7db8;'>This program comes with ABSOLUTELY NO WARRANTY.</p>
                <p style='color: #7a8dc9;'>This is free software, and you are welcome to redistribute it 
                under certain conditions.</p>
            </div>
            
            <h4 style='color: #3a4a6b;'>📌 重要条款摘要:</h4>
            <ul style='color: #5a6da7;'>
                <li>✅ 自由使用: 任何人都可以自由使用本软件</li>
                <li>✅ 自由修改: 可以修改软件代码</li>
                <li>✅ 自由分发: 可以重新分发软件</li>
                <li>🔓 强制开源: 任何分发或修改版本必须保持开源</li>
                <li>🚫 禁止闭源商业化: 不得将本软件用于闭源商业项目</li>
            </ul>
            
            <p style='text-align: center; margin-top: 20px;'>
                <a href='https://www.gnu.org/licenses/gpl-3.0.html' 
                   style='color: #4a6bda; text-decoration: none;'>
                    🌐 查看完整许可证文本
                </a>
            </p>
        </div>
        """

        license_browser.setHtml(license_html)
        license_browser.moveCursor(QTextCursor.Start)

        close_btn = QPushButton("关闭")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                background-color: #e0e6ff;
                color: #3a4a6b;
                border: 1px solid #b8c5ff;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #b8c5ff;
            }
        """)
        close_btn.clicked.connect(license_dialog.close)

        layout.addWidget(license_browser)
        layout.addWidget(close_btn, 0, Qt.AlignCenter)

        license_dialog.exec_()

