import sys
import os
import json
import datetime
from PyQt5.QtCore import QUrl, QTimer, Qt, QDir
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLineEdit, QAction, QMessageBox, QFileDialog, QLabel, QStyle
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import threading
import shutil

class BrowserTab(QWidget):
    def __init__(self, profile=None, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        self.profile = profile or QWebEngineProfile.defaultProfile()
        self.browser = QWebEngineView(self)
        self.page = QWebEnginePage(self.profile, self.browser)
        
        # Настройка настроек страницы
        settings = self.page.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        self.browser.setPage(self.page)
        
        self.layout.addWidget(self.browser)
        self.setLayout(self.layout)

    def set_url(self, url):
        self.browser.setUrl(QUrl(url))

    def get_url(self):
        return self.browser.url().toString()

    def load(self, url):
        self.browser.setUrl(QUrl(url))

class OpenSerfing(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.history = []
        self.cookie_store = QWebEngineProfile.defaultProfile().cookieStore()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("OpenSerfing Browser")
        self.setGeometry(300, 100, 1280, 720)
        
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_urlbar)
        
        self.tab_widget = QWidget()
        self.layout = QVBoxLayout()
        self.tab_widget.setLayout(self.layout)
        
        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        
        self.toolbar = QHBoxLayout()
        self.toolbar.setSpacing(10)
        
        self.back_btn = QPushButton()
        self.back_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowBack))
        self.back_btn.clicked.connect(self.navigate_back)

        self.forward_btn = QPushButton()
        self.forward_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowForward))
        self.forward_btn.clicked.connect(self.navigate_forward)

        self.reload_btn = QPushButton()
        self.reload_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.reload_btn.clicked.connect(self.reload_page)

        self.home_btn = QPushButton()
        self.home_btn.setIcon(self.style().standardIcon(QStyle.SP_DesktopIcon))
        self.home_btn.clicked.connect(self.navigate_home)

        self.toolbar.addWidget(self.back_btn)
        self.toolbar.addWidget(self.forward_btn)
        self.toolbar.addWidget(self.reload_btn)
        self.toolbar.addWidget(self.home_btn)
        self.toolbar.addWidget(self.urlbar)

        self.layout.addLayout(self.toolbar)
        self.layout.addWidget(self.tabs)
        
        self.setCentralWidget(self.tab_widget)
        
        self.status_bar = self.statusBar()
        
        self.add_tab(QUrl("https://www.google.com"), "Home")
        
        self.show()

    def add_tab(self, url=None, label="New Tab"):
        if url is None:
            url = QUrl("https://www.google.com")
            
        new_tab = BrowserTab(profile=QWebEngineProfile(self))
        new_tab.browser.load(url)
        index = self.tabs.addTab(new_tab, label)
        self.tabs.setCurrentIndex(index)
        
        new_tab.browser.urlChanged.connect(lambda url, tab=new_tab: self.update_tab_title(tab))
        new_tab.browser.titleChanged.connect(lambda title, tab=new_tab: self.tabs.setTabText(self.tabs.indexOf(tab), title))
        new_tab.browser.loadFinished.connect(self.update_urlbar)
        
        self.history.append(url.toString())

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)

    def navigate_to_url(self):
        url_text = self.urlbar.text()
        if not url_text.startswith("http"):
            url_text = "http://" + url_text
        self.tabs.currentWidget().set_url(QUrl(url_text))
        
    def update_urlbar(self):
        current_url = self.tabs.currentWidget().get_url()
        self.urlbar.setText(current_url)
        self.urlbar.setCursorPosition(0)
        
    def update_tab_title(self, tab):
        self.tabs.setTabText(self.tabs.indexOf(tab), tab.browser.title())

    def navigate_back(self):
        self.tabs.currentWidget().browser.back()

    def navigate_forward(self):
        self.tabs.currentWidget().browser.forward()

    def reload_page(self):
        self.tabs.currentWidget().browser.reload()

    def navigate_home(self):
        self.tabs.currentWidget().browser.setUrl(QUrl("https://www.google.com"))

    def set_user_agent(self, agent):
        self.tabs.currentWidget().page.profile().setHttpUserAgent(agent)

    def handle_profile(self):
        os_name = os.name
        data_dir = QDir.homePath()
        if os_name == "nt":
            data_dir += "/AppData/Local/OpenSerfing"
        elif os_name == "posix":
            data_dir += "/.openserfing"
        else:
            data_dir += "/OpenSerfing"
        
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        QWebEngineProfile.defaultProfile().setCachePath(data_dir)
        QWebEngineProfile.defaultProfile().setPersistentStoragePath(data_dir)
        self.cookie_store.deleteAllCookies()

    def save_history(self):
        history_path = QDir.homePath() + "/.openserfing/history.json"
        with open(history_path, "w") as f:
            json.dump(self.history, f)

    def load_history(self):
        history_path = QDir.homePath() + "/.openserfing/history.json"
        if os.path.exists(history_path):
            with open(history_path, "r") as f:
                self.history = json.load(f)

    def closeEvent(self, event):
        self.save_history()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OpenSerfing()
    window.handle_profile()
    window.load_history()
    sys.exit(app.exec_())
