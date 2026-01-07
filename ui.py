from __future__ import annotations

import sys
import locale
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit,
    QComboBox, QPushButton, QProgressBar, QListWidget, QCheckBox,
    QLabel, QHBoxLayout, QSpacerItem, QSizePolicy, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


LANGS = [
    ("Türkçe", "tr"),
    ("English", "en"),
    ("Deutsch", "de"),
    ("Español", "es"),
    ("Français", "fr"),
    ("Italiano", "it"),
    ("日本語", "ja"),
    ("中文", "zh"),
    ("Русский", "ru"),
]


def _norm_lang(code: str) -> str:
    code = (code or "").lower()
    return code.split("_")[0].split("-")[0][:2]


def detect_lang_code() -> str:
    raw = ""
    try:
        raw = locale.getlocale()[0] or ""
    except Exception:
        raw = ""

    if not raw:
        try:
            raw = locale.getdefaultlocale()[0] or ""
        except Exception:
            raw = ""

    code = _norm_lang(raw)
    allowed = {c for _, c in LANGS}
    return code if code in allowed else "en"


class MediaDownloaderUI(QMainWindow):
    folder_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Downloader")
        self.resize(700, 820)
        self.download_folder = "İndirilenler"
        self.setup_ui()
        self.apply_modern_style()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setSpacing(18)
        layout.setContentsMargins(30, 30, 30, 30)

        self.title_label = QLabel("Media Downloader")
        self.title_label.setObjectName("title_label")
        self.title_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: #64b5f6; margin-bottom: 10px;")
        layout.addWidget(self.title_label)

        # URL row + Check
        url_row = QHBoxLayout()

        self.url_input = QLineEdit()
        self.url_input.setObjectName("url_input")
        self.url_input.setPlaceholderText("YouTube, Instagram, TikTok, Twitter vb. bağlantı yapıştır...")
        self.url_input.setFixedHeight(50)

        self.check_button = QPushButton("Kontrol")
        self.check_button.setObjectName("check_btn")
        self.check_button.setFixedHeight(50)
        self.check_button.setFixedWidth(140)

        url_row.addWidget(self.url_input, 1)
        url_row.addWidget(self.check_button, 0)
        layout.addLayout(url_row)

        # Format row (NO "best" texts)
        format_layout = QHBoxLayout()

        self.format_label = QLabel("Format:")
        self.format_label.setObjectName("format_label")

        self.format_combo = QComboBox()
        self.format_combo.setObjectName("format_combo")
        self.format_combo.setFixedHeight(48)
        self.format_combo.addItems([
            "MP3",
            "WAV",
            "FLAC",
            "MP4",
            "WEBM",
        ])
        # default: MP4
        self.format_combo.setCurrentIndex(self.format_combo.findText("MP4"))

        format_layout.addWidget(self.format_label)
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)

        # Quality row (NO "best/lowest")
        quality_layout = QHBoxLayout()

        self.quality_label = QLabel("Kalite:")
        self.quality_label.setObjectName("quality_label")

        self.quality_combo = QComboBox()
        self.quality_combo.setObjectName("quality_combo")
        self.quality_combo.setFixedHeight(48)
        self.quality_combo.addItems([
            "2160p",
            "1440p",
            "1080p",
            "720p",
            "480p",
            "360p",
        ])
        # default: 1080p
        self.quality_combo.setCurrentIndex(self.quality_combo.findText("1080p"))

        quality_layout.addWidget(self.quality_label)
        quality_layout.addWidget(self.quality_combo)
        layout.addLayout(quality_layout)

        # Folder row
        folder_layout = QHBoxLayout()

        self.folder_label = QLabel(f"Klasör: {self.download_folder}")
        self.folder_label.setObjectName("folder_label")
        self.folder_label.setStyleSheet("color: #b0bec5;")

        self.folder_button = QPushButton("Klasör Seç")
        self.folder_button.setObjectName("folder_btn")
        self.folder_button.setFixedHeight(48)
        self.folder_button.clicked.connect(self.choose_folder)

        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.folder_button)
        layout.addLayout(folder_layout)

        # Playlist section
        self.playlist_label = QLabel("Playlist / Videolar")
        self.playlist_label.setObjectName("playlist_label")
        self.playlist_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))

        search_layout = QHBoxLayout()

        self.playlist_search = QLineEdit()
        self.playlist_search.setObjectName("playlist_search")
        self.playlist_search.setPlaceholderText("Listede ara...")
        self.playlist_search.setFixedHeight(46)

        self.select_all_cb = QCheckBox("Hepsini Seç")
        self.select_all_cb.setObjectName("select_all_cb")
        self.select_all_cb.setChecked(True)

        search_layout.addWidget(self.playlist_search, 1)
        search_layout.addWidget(self.select_all_cb, 0)

        self.playlist_list = QListWidget()
        self.playlist_list.setObjectName("playlist_list")
        self.playlist_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.playlist_list.setMinimumHeight(200)
        self.playlist_list.setMaximumHeight(250)

        layout.addWidget(self.playlist_label)
        layout.addLayout(search_layout)
        layout.addWidget(self.playlist_list)

        # Progress + info
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progress_bar")
        self.progress_bar.setFixedHeight(40)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setValue(0)

        self.info_label = QLabel("Hazır")
        self.info_label.setObjectName("info_label")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setFont(QFont("Segoe UI", 11))

        layout.addWidget(self.progress_bar)
        layout.addWidget(self.info_label)

        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Bottom row: language (right)
        bottom_row = QHBoxLayout()
        bottom_row.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.lang_label = QLabel("Dil:")
        self.lang_label.setObjectName("lang_label")
        self.lang_label.setStyleSheet("color: #b0bec5;")

        self.lang_combo = QComboBox()
        self.lang_combo.setObjectName("lang_combo")
        self.lang_combo.setFixedHeight(44)
        self.lang_combo.setFixedWidth(220)

        for name, code in LANGS:
            self.lang_combo.addItem(name, code)

        sys_code = detect_lang_code()
        idx = self.lang_combo.findData(sys_code)
        self.lang_combo.setCurrentIndex(idx if idx >= 0 else self.lang_combo.findData("en"))

        bottom_row.addWidget(self.lang_label)
        bottom_row.addWidget(self.lang_combo)
        layout.addLayout(bottom_row)

        # Download button
        self.download_button = QPushButton("İndirmeye Başla")
        self.download_button.setObjectName("download_button")
        self.download_button.setFixedHeight(60)
        self.download_button.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(self.download_button)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "İndirme Klasörünü Seç", self.download_folder)
        if folder:
            self.download_folder = folder
            self.folder_label.setText(f"Klasör: {folder}")
            self.folder_selected.emit(folder)

    def apply_modern_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QLabel { color: #e0e0e0; }
            QLineEdit, QComboBox {
                background-color: #1e1e1e;
                border: 2px solid #333333;
                border-radius: 16px;
                padding: 12px 16px;
                color: #ffffff;
                font-size: 13pt;
            }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #64b5f6; }
            QLineEdit#playlist_search { padding: 8px 14px; font-size: 12pt; }
            QComboBox { padding-right: 40px; }
            QComboBox::drop-down { border: none; width: 40px; border-left: 1px solid #333; }
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDFMNiA2TDExIDEiIHN0cm9rZT0iI2I3YjdiNyIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz4KPC9zdmc+);
            }
            QListWidget {
                background-color: #1e1e1e;
                border: 2px solid #333333;
                border-radius: 16px;
                color: #ffffff;
                padding: 8px;
                font-size: 12pt;
            }
            QListWidget::item { padding: 12px; border-bottom: 1px solid #2d2d2d; }
            QListWidget::item:selected { background-color: #64b5f6; color: #121212; }

            QProgressBar {
                background-color: #1e1e1e;
                border: 2px solid #333333;
                border-radius: 20px;
                text-align: center;
                font-size: 13pt;
                color: white;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #0d47a1,
                    stop: 1 #1976d2
                );
                border-radius: 18px;
            }

            QPushButton {
                background: linear-gradient(to bottom, #1e5aa8, #0d47a1);
                border: none;
                border-radius: 30px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover { background: linear-gradient(to bottom, #2a6bc2, #1565c0); }
            QPushButton:pressed { background: #0b3d91; }
            QPushButton#folder_btn { background: #2d2d2d; }
            QPushButton#folder_btn:hover { background: #3d3d3d; }
            QPushButton#check_btn { border-radius: 18px; }
            QCheckBox { color: #e0e0e0; font-size: 12pt; }
            QCheckBox::indicator {
                width: 20px; height: 20px;
                border-radius: 6px;
                border: 2px solid #555;
            }
            QCheckBox::indicator:checked { background-color: #64b5f6; border-color: #64b5f6; }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MediaDownloaderUI()
    window.show()
    sys.exit(app.exec())
