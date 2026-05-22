#!/usr/bin/env python3
"""
Simple Image & Video Viewer with Qt - Unlimited Undo
"""

import shutil
import sys
from curses import KEY_BACKSPACE
from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QKeyEvent, QPixmap
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

try:
    from send2trash import send2trash

    HAS_SEND2TRASH = True
except ImportError:
    HAS_SEND2TRASH = False


class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.image_files: List[Path] = []
        self.current_index: int = -1
        self.current_folder: Optional[Path] = None
        self.undo_buffer: List[Path] = []

        # Media Player for videos
        self.media_player = QMediaPlayer()
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)

        # Stacked widget to switch between image and video
        self.display_stack = QStackedWidget()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #1e1e1e;")
        self.image_label.setMinimumSize(800, 500)

        self.display_stack.addWidget(self.image_label)
        self.display_stack.addWidget(self.video_widget)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(10)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_prev = QPushButton("Previous (P / ← / Backspace)")
        self.btn_next = QPushButton("Next (N / → / Enter / Space)")
        self.btn_delete = QPushButton("Delete (D / Del)")
        self.btn_undo = QPushButton("Undo (U / Ctrl+Z)")
        self.btn_open = QPushButton("Open Folder (O)")
        self.btn_help = QPushButton("Help (F1)")

        for btn in (
            self.btn_prev,
            self.btn_next,
            self.btn_delete,
            self.btn_undo,
            self.btn_open,
            self.btn_help,
        ):
            btn.setFont(QFont("Arial", 18, QFont.Weight.Bold))
            btn.setMinimumHeight(200)
            btn.setMaximumHeight(200)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn_layout.addWidget(btn)

        main_layout.addLayout(btn_layout)

        # Filename label
        self.filename_label = QLabel()
        self.filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.filename_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.filename_label.setStyleSheet("padding: 8px;")
        main_layout.addWidget(self.filename_label)

        # Display area
        main_layout.addWidget(self.display_stack, stretch=1)

        # Connections
        self.btn_prev.clicked.connect(self.prev_item)
        self.btn_next.clicked.connect(self.next_item)
        self.btn_delete.clicked.connect(self.delete_current)
        self.btn_undo.clicked.connect(self.undo_delete)
        self.btn_open.clicked.connect(self.open_folder_dialog)
        self.btn_help.clicked.connect(self.show_help)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.image_label.setFocus()

        self.showMaximized()

        self.open_folder_dialog(preselect_current=True)

    def show_help(self):
        help_text = """
<h2>Image & Video Viewer - Keyboard Shortcuts</h2>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width:100%">
    <tr><th>Action</th><th>Keys</th></tr>
    <tr><td>Next</td><td><b>Right Arrow</b>, N, Enter</td></tr>
    <tr><td>Previous</td><td><b>Left Arrow</b>, P</td></tr>
    <tr><td>Skip +10</td><td><b>Down Arrow</b>, Page Down</td></tr>
    <tr><td>Skip -10</td><td><b>Up Arrow</b>, Page Up</td></tr>
    <tr><td>First Item</td><td><b>Home</b></td></tr>
    <tr><td>Delete</td><td><b>D</b>, Delete</td></tr>
    <tr><td>Undo</td><td><b>U</b>, Ctrl + Z</td></tr>
    <tr><td>Open Folder</td><td><b>O</b></td></tr>
    <tr><td>Help</td><td><b>F1</b></td></tr>
</table>
<p><b>Supported:</b> Images (.jpg, .png, ...) and Videos (.mp4, .mov, .mkv, .avi, .webm, ...)</p>
"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Help")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    # ==================== Folder ====================
    def open_folder_dialog(self, preselect_current: bool = False):
        start_dir = str(self.current_folder) if self.current_folder else str(Path.cwd())
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder", start_dir, QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.load_folder(Path(folder))

    def load_folder(self, folder: Path, clear_undo: bool = True):
        self.current_folder = folder
        if clear_undo:
            self.undo_buffer.clear()

        self.image_files = []
        image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif"}
        video_exts = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".m4v"}

        for file in sorted(folder.iterdir()):
            if file.is_file() and file.suffix.lower() in image_exts | video_exts:
                self.image_files.append(file)

        if not self.image_files:
            QMessageBox.warning(
                self, "No Media", "No images or videos found in folder."
            )
            self.clear_display()
            return

        self.current_index = 0
        self.show_current_item()

    def clear_display(self):
        self.display_stack.setCurrentWidget(self.image_label)
        self.image_label.setText("No media files")
        self.filename_label.setText("")
        self.setWindowTitle("Media Viewer")
        self.media_player.stop()

    def show_current_item(self):
        if not self.image_files or self.current_index < 0:
            self.clear_display()
            return

        path = self.image_files[self.current_index]
        filename = path.name
        suffix = path.suffix.lower()

        self.setWindowTitle(f"{filename} - Media Viewer")
        self.filename_label.setText(filename)

        # Stop any playing video
        self.media_player.stop()

        if suffix in {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".webp",
            ".tiff",
            ".tif",
        }:
            # Show Image
            self.display_stack.setCurrentWidget(self.image_label)
            pixmap = QPixmap(str(path))
            if pixmap.isNull():
                self.image_label.setText("Failed to load image")
            else:
                scaled = pixmap.scaled(
                    self.image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.image_label.setPixmap(scaled)
        else:
            # Show Video
            self.display_stack.setCurrentWidget(self.video_widget)
            self.media_player.setSource(QUrl.fromLocalFile(str(path)))
            self.media_player.play()

    # ==================== Navigation ====================
    def go_to_index(self, index: int):
        if not self.image_files:
            return
        self.current_index = max(0, min(index, len(self.image_files) - 1))
        self.show_current_item()

    def next_item(self):
        if self.image_files:
            self.current_index = (self.current_index + 1) % len(self.image_files)
            self.show_current_item()

    def prev_item(self):
        if self.image_files:
            self.current_index = (self.current_index - 1) % len(self.image_files)
            self.show_current_item()

    def skip_items(self, steps: int):
        if self.image_files:
            self.go_to_index(self.current_index + steps)

    # ==================== Delete & Undo ====================
    def get_backup_folder(self) -> Path:
        backup = self.current_folder / ".media_viewer_undo"
        backup.mkdir(exist_ok=True)
        return backup

    def delete_current(self):
        if not self.image_files or self.current_index < 0:
            return

        file_to_delete = self.image_files[self.current_index]

        try:
            backup_folder = self.get_backup_folder()
            backup_path = backup_folder / file_to_delete.name

            shutil.copy2(file_to_delete, backup_path)
            self.undo_buffer.append(backup_path)

            if HAS_SEND2TRASH:
                send2trash(str(file_to_delete))
            else:
                file_to_delete.unlink()

            del self.image_files[self.current_index]

            if not self.image_files:
                self.clear_display()
                self.current_index = -1
                return

            if self.current_index >= len(self.image_files):
                self.current_index = len(self.image_files) - 1

            self.show_current_item()

        except Exception as e:
            QMessageBox.critical(self, "Delete Error", str(e))

    def undo_delete(self):
        if not self.undo_buffer:
            QMessageBox.information(self, "Undo", "Nothing to undo.")
            return

        backup_path = self.undo_buffer.pop()

        try:
            if not backup_path.exists():
                QMessageBox.warning(self, "Undo", "Backup file no longer exists.")
                return

            original_path = self.current_folder / backup_path.name
            shutil.move(str(backup_path), str(original_path))

            current_name = original_path.name
            self.load_folder(self.current_folder, clear_undo=False)

            for i, f in enumerate(self.image_files):
                if f.name == current_name:
                    self.current_index = i
                    break
            else:
                self.current_index = max(0, len(self.image_files) - 1)

            self.show_current_item()

        except Exception as e:
            QMessageBox.critical(self, "Undo Failed", str(e))

    # ==================== Keyboard ====================
    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key.Key_F1:
            self.show_help()
            return

        if (modifiers & Qt.KeyboardModifier.ControlModifier) and key == Qt.Key.Key_Z:
            self.undo_delete()
            return

        if key in (
            Qt.Key.Key_Right,
            Qt.Key.Key_N,
            Qt.Key.Key_Enter,
            Qt.Key.Key_Return,
            Qt.Key.Key_Space,
        ):
            self.next_item()
        elif key in (Qt.Key.Key_Left, Qt.Key.Key_P, Qt.Key.Key_Backspace):
            self.prev_item()
        elif key == Qt.Key.Key_Down or key == Qt.Key.Key_PageDown:
            self.skip_items(10)
        elif key == Qt.Key.Key_Up or key == Qt.Key.Key_PageUp:
            self.skip_items(-10)
        elif key == Qt.Key.Key_Home:
            self.go_to_index(0)
        elif key in (Qt.Key.Key_D, Qt.Key.Key_Delete):
            self.delete_current()
        elif key == Qt.Key.Key_U:
            self.undo_delete()
        elif key == Qt.Key.Key_O:
            self.open_folder_dialog()
        else:
            super().keyPressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Required for multimedia
    app.setStyle("Fusion")
    viewer = ImageViewer()
    viewer.show()
    sys.exit(app.exec())
