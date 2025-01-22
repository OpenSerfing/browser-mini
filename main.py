#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt6.QtCore import QUrl, Qt, QDir
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QLineEdit, QStatusBar,
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QProgressBar, QPushButton, QFileDialog
)
from PyQt6.QtGui import (
    QAction, QPalette, QColor, QFont, QLinearGradient, 
    QPainter, QBrush
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEngineSettings
)

# Определение цветовой схемы
COLORS = {
    'background': QColor(18, 18, 18),
    'foreground': QColor(255, 255, 255),
    'accent1': QColor(0, 150, 199),  # Синий
    'accent2': QColor(0, 199, 150),  # Зеленый
    'surface': QColor(30, 30, 30),
    'surface_light': QColor(45, 45, 45),
}

class CustomToolBar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QToolBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #00506B, stop:1 #005B47);
                border: none;
                padding: 5px;
            }
            QToolButton {
                background: transparent;
                border: none;
                color: white;
                padding: 5px;
                margin: 2px;
                border-radius: 3px;
            }
            QToolButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QToolButton:pressed {
                background: rgba(255, 255, 255, 0.2);
            }
        """)

class CustomLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QLineEdit {
                background: #2A2A2A;
                border: 1px solid #3A3A3A;
                border-radius: 5px;
                color: white;
                padding: 5px;
                selection-background-color: #005B47;
            }
            QLineEdit:focus {
                border: 1px solid #00506B;
            }
        """)

class DownloadManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Загрузки')
        self.setGeometry(200, 200, 600, 400)
        self.setup_ui()
        self.downloads = {}

    def setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background: #121212;
                color: white;
            }
            QTableWidget {
                background: #1A1A1A;
                color: white;
                gridline-color: #2A2A2A;
                border: none;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background: #2A2A2A;
                color: white;
                padding: 5px;
                border: none;
            }
            QProgressBar {
                border: none;
                background: #2A2A2A;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #00506B, stop:1 #005B47);
            }
        """)
        
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(['Файл', 'Прогресс', 'Статус'])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

    def add_download(self, download):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        filename = QTableWidgetItem(os.path.basename(download.downloadFileName()))
        self.table.setItem(row, 0, filename)
        
        progress = QProgressBar()
        self.table.setCellWidget(row, 1, progress)
        
        status = QTableWidgetItem('Загрузка...')
        self.table.setItem(row, 2, status)
        
        self.downloads[download] = {'row': row, 'progress': progress}
        
        download.downloadProgress.connect(
            lambda rcv, tot, d=download: self.update_progress(d, rcv, tot)
        )
        download.finished.connect(
            lambda d=download: self.download_finished(d)
        )

    def update_progress(self, download, received, total):
        if download in self.downloads:
            progress = self.downloads[download]['progress']
            progress.setRange(0, total)
            progress.setValue(received)

    def download_finished(self, download):
        if download in self.downloads:
            row = self.downloads[download]['row']
            self.table.setItem(row, 2, QTableWidgetItem('Завершено'))
            del self.downloads[download]

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_connections()
        self.apply_theme()

    def setup_ui(self):
        self.setWindowTitle('Aurora Browser')
        self.setGeometry(100, 100, 1200, 800)

        # Панель навигации
        nav_bar = CustomToolBar()
        self.addToolBar(nav_bar)

        # Кнопки навигации
        self.back_btn = QAction('←', self)
        self.forward_btn = QAction('→', self)
        self.reload_btn = QAction('↻', self)
        self.home_btn = QAction('🏠', self)
        self.downloads_btn = QAction('↓', self)
        
        nav_bar.addAction(self.back_btn)
        nav_bar.addAction(self.forward_btn)
        nav_bar.addAction(self.reload_btn)
        nav_bar.addAction(self.home_btn)
        nav_bar.addAction(self.downloads_btn)

        # Адресная строка
        self.url_bar = CustomLineEdit()
        nav_bar.addWidget(self.url_bar)

        # Веб-движок
        self.web = QWebEngineView()
        
        # Настройка профиля
        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.downloadRequested.connect(self.handle_download)
        
        # Включаем звук
        settings = self.web.page().settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        
        self.setCentralWidget(self.web)

        # Статус бар
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.setStyleSheet("""
            QStatusBar {
                background: #1A1A1A;
                color: white;
            }
        """)

        # Менеджер загрузок
        self.download_manager = DownloadManager(self)

        # Загружаем стартовую страницу
        self.navigate_home()

    def apply_theme(self):
        # Установка шрифта Comfortaa
        font = QFont("Comfortaa", 10)
        QApplication.setFont(font)

        # Установка темной темы
        self.setStyleSheet("""
            QMainWindow {
                background: #121212;
                color: white;
            }
            QWidget {
                background: #121212;
                color: white;
            }
            QMenu {
                background: #1A1A1A;
                color: white;
                border: 1px solid #2A2A2A;
            }
            QMenu::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #00506B, stop:1 #005B47);
            }
            QToolTip {
                background: #1A1A1A;
                color: white;
                border: 1px solid #2A2A2A;
            }
        """)

    def setup_connections(self):
        self.back_btn.triggered.connect(self.web.back)
        self.forward_btn.triggered.connect(self.web.forward)
        self.reload_btn.triggered.connect(self.web.reload)
        self.home_btn.triggered.connect(self.navigate_home)
        self.downloads_btn.triggered.connect(self.download_manager.show)
        self.url_bar.returnPressed.connect(self.navigate_to_url)

        self.web.urlChanged.connect(self.update_url)
        self.web.titleChanged.connect(self.update_title)
        
        self.web.loadStarted.connect(lambda: self.status.showMessage('Загрузка...'))
        self.web.loadProgress.connect(lambda p: self.status.showMessage(f'Загрузка... {p}%'))
        self.web.loadFinished.connect(lambda: self.status.clearMessage())

    def handle_download(self, download):
        path, _ = QFileDialog.getSaveFileName(
            self, 
            'Сохранить файл',
            QDir.homePath() + "/" + download.suggestedFileName()
        )
        
        if path:
            download.setDownloadDirectory(os.path.dirname(path))
            download.setDownloadFileName(os.path.basename(path))
            download.accept()
            self.download_manager.add_download(download)
            if not self.download_manager.isVisible():
                self.download_manager.show()

    def navigate_home(self):
        self.web.setUrl(QUrl('https://www.google.com'))

    def navigate_to_url(self):
        url = self.url_bar.text()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        self.web.setUrl(QUrl(url))

    def update_url(self, url):
        self.url_bar.setText(url.toString())

    def update_title(self, title):
        self.setWindowTitle(f'{title} - Aurora Browser')

def main():
    app = QApplication(sys.argv)
    
    # Установка глобальных стилей приложения
    app.setStyle('Fusion')
    
    # Установка темной палитры
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, COLORS['background'])
    palette.setColor(QPalette.ColorRole.WindowText, COLORS['foreground'])
    palette.setColor(QPalette.ColorRole.Base, COLORS['surface'])
    palette.setColor(QPalette.ColorRole.AlternateBase, COLORS['surface_light'])
    palette.setColor(QPalette.ColorRole.ToolTipBase, COLORS['surface'])
    palette.setColor(QPalette.ColorRole.ToolTipText, COLORS['foreground'])
    palette.setColor(QPalette.ColorRole.Text, COLORS['foreground'])
    palette.setColor(QPalette.ColorRole.Button, COLORS['surface'])
    palette.setColor(QPalette.ColorRole.ButtonText, COLORS['foreground'])
    palette.setColor(QPalette.ColorRole.Link, COLORS['accent1'])
    palette.setColor(QPalette.ColorRole.Highlight, COLORS['accent2'])
    app.setPalette(palette)
    
    browser = Browser()
    browser.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()