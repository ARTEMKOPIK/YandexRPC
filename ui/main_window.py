"""
Main UI window module.
Provides PyQt6-based graphical interface for WinYandexMusicRPC.
"""

import sys
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QCheckBox, QGroupBox, QSystemTrayIcon,
    QMenu, QAction, QSpinBox, QMessageBox, QFormLayout, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap

from ..core.app_state import (
    get_app_state, AppState, ActivityTypeConfig, ButtonConfig, 
    LanguageConfig, LogType
)
from ..core.media_manager import MediaInfoProvider
from ..utils.logger import log
from ..utils.async_utils import run_async


class MainWindow(QMainWindow):
    """Main application window with settings controls."""
    
    # Signals
    settings_changed = pyqtSignal()
    
    def __init__(self, config_manager=None):
        super().__init__()
        
        self._app_state = get_app_state()
        self.config_manager = config_manager
        self.media_provider = MediaInfoProvider()
        
        self.setWindowTitle("WinYandexMusicRPC Settings")
        self.setFixedSize(500, 400)
        
        # Setup system tray
        self._setup_tray_icon()
        
        # Setup UI
        self._setup_ui()
        
        # Load current settings
        self._load_settings_to_ui()
        
        # Auto-hide to tray after 3 seconds
        QTimer.singleShot(3000, self.hide_to_tray)
    
    def _setup_tray_icon(self):
        """Setup system tray icon and menu."""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Try to load icon from assets
        try:
            icon = QIcon("assets/YMRPC_ico.ico")
            if not icon.isNull():
                self.tray_icon.setIcon(icon)
            else:
                self.tray_icon.setIcon(self.style().standardIcon(
                    QSystemTrayIcon.StandardIcon.MusicIcon
                ))
        except Exception:
            self.tray_icon.setIcon(self.style().standardIcon(
                QSystemTrayIcon.StandardIcon.MusicIcon
            ))
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show Settings", self)
        show_action.triggered.connect(self.show_from_tray)
        tray_menu.addAction(show_action)
        
        restart_action = QAction("Restart RPC", self)
        restart_action.triggered.connect(self._restart_rpc)
        tray_menu.addAction(restart_action)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()
    
    def _setup_ui(self):
        """Setup the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("🎵 WinYandexMusicRPC Settings")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # Activity Type Group
        activity_group = QGroupBox("Activity Type")
        activity_layout = QFormLayout()
        
        self.activity_combo = QComboBox()
        self.activity_combo.addItems(["Listening", "Playing"])
        activity_layout.addRow("Display as:", self.activity_combo)
        
        activity_group.setLayout(activity_layout)
        layout.addWidget(activity_group)
        
        # Buttons Configuration Group
        buttons_group = QGroupBox("Buttons Configuration")
        buttons_layout = QFormLayout()
        
        self.buttons_combo = QComboBox()
        self.buttons_combo.addItems([
            "Both (Web + App)",
            "Yandex Music Web Only",
            "Yandex Music App Only",
            "No Buttons"
        ])
        buttons_layout.addRow("Show buttons:", self.buttons_combo)
        
        buttons_group.setLayout(buttons_layout)
        layout.addWidget(buttons_group)
        
        # Language Group
        language_group = QGroupBox("Language")
        language_layout = QFormLayout()
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Russian"])
        language_layout.addRow("Interface language:", self.language_combo)
        
        language_group.setLayout(language_layout)
        layout.addWidget(language_group)
        
        # Search Settings Group
        search_group = QGroupBox("Search Settings")
        search_layout = QFormLayout()
        
        self.strong_find_check = QCheckBox("Strong match (exact artist/title)")
        self.strong_find_check.setChecked(True)
        search_layout.addRow("", self.strong_find_check)
        
        # Session selection
        self.session_combo = QComboBox()
        self.session_combo.addItem("Automatic")
        self._refresh_sessions_button = QPushButton("Refresh Sessions")
        self._refresh_sessions_button.clicked.connect(self._refresh_sessions)
        
        session_layout = QHBoxLayout()
        session_layout.addWidget(self.session_combo)
        session_layout.addWidget(self._refresh_sessions_button)
        search_layout.addRow("Media Source:", session_layout)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Auto-start
        self.auto_start_check = QCheckBox("Start with Windows")
        layout.addWidget(self.auto_start_check)
        
        # Save button
        save_button = QPushButton("💾 Save Settings")
        save_button.clicked.connect(self._save_settings)
        save_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "padding: 10px; font-weight: bold; border-radius: 5px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        layout.addWidget(save_button)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
    
    def _load_settings_to_ui(self):
        """Load current settings into UI controls."""
        # Activity type
        if self._app_state.activity_type_config == ActivityTypeConfig.LISTENING:
            self.activity_combo.setCurrentIndex(0)
        else:
            self.activity_combo.setCurrentIndex(1)
        
        # Buttons config
        button_mapping = {
            ButtonConfig.BOTH: 0,
            ButtonConfig.YANDEX_MUSIC_WEB: 1,
            ButtonConfig.YANDEX_MUSIC_APP: 2,
            ButtonConfig.NEITHER: 3
        }
        self.buttons_combo.setCurrentIndex(
            button_mapping.get(self._app_state.button_config, 0)
        )
        
        # Language
        if self._app_state.language_config == LanguageConfig.ENGLISH:
            self.language_combo.setCurrentIndex(0)
        else:
            self.language_combo.setCurrentIndex(1)
        
        # Strong find
        self.strong_find_check.setChecked(self._app_state.strong_find)
        
        # Auto-start
        self.auto_start_check.setChecked(self._app_state.auto_start_windows)
        
        # Load sessions
        self._refresh_sessions()
    
    async def _get_available_sessions(self):
        """Get available media sessions asynchronously."""
        try:
            return await self.media_provider.get_session_ids()
        except Exception as e:
            log(f"Failed to get sessions: {e}", LogType.Error)
            return []
    
    def _refresh_sessions(self):
        """Refresh the list of available media sessions."""
        try:
            sessions = run_async(self._get_available_sessions(), timeout=5)
            
            # Clear and repopulate combo
            self.session_combo.clear()
            self.session_combo.addItem("Automatic")
            
            current_session = self.config_manager.get_selected_session() if self.config_manager else "Automatic"
            
            for session in sessions:
                self.session_combo.addItem(session)
                if session == current_session:
                    self.session_combo.setCurrentText(session)
            
            self.status_label.setText(f"Found {len(sessions)} media session(s)")
            
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
    
    def _save_settings(self):
        """Save current UI settings to configuration."""
        try:
            # Activity type
            activity_index = self.activity_combo.currentIndex()
            self._app_state.activity_type_config = (
                ActivityTypeConfig.LISTENING if activity_index == 0 
                else ActivityTypeConfig.PLAYING
            )
            
            # Buttons config
            button_mapping = {
                0: ButtonConfig.BOTH,
                1: ButtonConfig.YANDEX_MUSIC_WEB,
                2: ButtonConfig.YANDEX_MUSIC_APP,
                3: ButtonConfig.NEITHER
            }
            self._app_state.button_config = button_mapping[
                self.buttons_combo.currentIndex()
            ]
            
            # Language
            self._app_state.language_config = (
                LanguageConfig.ENGLISH if self.language_combo.currentIndex() == 0
                else LanguageConfig.RUSSIAN
            )
            
            # Strong find
            self._app_state.strong_find = self.strong_find_check.isChecked()
            
            # Selected session
            selected_session = self.session_combo.currentText()
            if self.config_manager:
                self.config_manager.set_selected_session(selected_session)
            
            # Auto-start (Windows only)
            if sys.platform == "win32":
                self._set_auto_start(self.auto_start_check.isChecked())
            
            # Save to config file
            if self.config_manager:
                self.config_manager.set_enum_setting(
                    'UserSettings', 'activity_type', 
                    self._app_state.activity_type_config
                )
                self.config_manager.set_enum_setting(
                    'UserSettings', 'buttons_settings', 
                    self._app_state.button_config
                )
                self.config_manager.set_enum_setting(
                    'UserSettings', 'language', 
                    self._app_state.language_config
                )
                self.config_manager.set_setting(
                    'UserSettings', 'strong_find',
                    str(self._app_state.strong_find)
                )
            
            # Trigger restart
            self._app_state.need_restart = True
            
            self.status_label.setText("✅ Settings saved! Restarting RPC...")
            log("Settings saved successfully", LogType.Notification)
            
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
            log(f"Failed to save settings: {e}", LogType.Error)
    
    def _set_auto_start(self, enable: bool):
        """Enable/disable auto-start on Windows."""
        if sys.platform != "win32":
            return
        
        try:
            import winreg
            import os
            
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "YaMusicRPC"
            app_path = f'"{sys.executable}" "{sys.argv[0]}"'
            
            if enable:
                # Add to registry
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, key_path, 0,
                    winreg.KEY_WRITE
                )
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
                winreg.CloseKey(key)
            else:
                # Remove from registry
                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER, key_path, 0,
                        winreg.KEY_WRITE
                    )
                    winreg.DeleteValue(key, app_name)
                    winreg.CloseKey(key)
                except FileNotFoundError:
                    pass
            
            self._app_state.auto_start_windows = enable
            
        except Exception as e:
            log(f"Failed to set auto-start: {e}", LogType.Error)
    
    def _restart_rpc(self):
        """Request RPC restart."""
        self._app_state.need_restart = True
        self.status_label.setText("🔄 Restarting RPC...")
        log("RPC restart requested", LogType.Notification)
    
    def _quit_application(self):
        """Quit the application."""
        QApplication.quit()
    
    def _on_tray_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_from_tray()
    
    def show_from_tray(self):
        """Show window from system tray."""
        self.show()
        self.activateWindow()
        self.raise_()
    
    def hide_to_tray(self):
        """Hide window to system tray."""
        if self._app_state.icon_tray:
            self.hide()
    
    def closeEvent(self, event):
        """Handle window close event."""
        event.ignore()
        self.hide_to_tray()
