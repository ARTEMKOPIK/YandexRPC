"""
WinYandexMusicRPC - Discord Rich Presence for Yandex Music on Windows.

Main entry point for the refactored application with improved architecture.
"""

import multiprocessing
import subprocess
import webbrowser
import sys
import os
import time
import threading
import re
import json

import psutil
import pystray
import win32gui
import win32con
import win32console
import winreg
from PIL import Image
from win32com.client import Dispatch

# Import refactored modules
from config_manager import ConfigManager
from core.app_state import (
    initialize_app_state, 
    get_app_state, 
    ActivityTypeConfig, 
    ButtonConfig, 
    LanguageConfig,
    LogType
)
from core.presence_service import PresenceService
from core.exceptions import TokenError
from utils.logger import log
from utils.async_utils import run_async
from utils.string_utils import blur_string

# Import token getter
import getToken


class Application:
    """Main application class that orchestrates all components."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.app_state = initialize_app_state(self.config_manager)
        self.presence_service = PresenceService()
        self.icon_tray = None
        self.result_queue = multiprocessing.Queue()
        self.window = None
    
    def run(self):
        """Run the main application."""
        try:
            if self._is_run_by_exe():
                self._setup_exe_mode()
            else:
                log("Launched without minimizing to tray and other GUI functions")
            
            # Load settings
            self.app_state.load_settings(from_start=True)
            
            # Initialize token
            self._initialize_token(force_get=False)
            
            # Start presence service
            self.presence_service.start()
            
        except KeyboardInterrupt:
            log("Keyboard interrupt received, stopping...")
            self.presence_service.stop()
    
    def _is_run_by_exe(self):
        return sys.argv[0].endswith('.exe')
    
    def _setup_exe_mode(self):
        log("Launched. Check the actual version...")
        self._check_latest_version()
        
        self.window = win32console.GetConsoleWindow()
        
        if self._is_already_running():
            log("WinYandexMusicRPC is already running.", LogType.Error)
            self._show_console_permanent()
            self._wait_and_exit()
        
        win32console.SetConsoleTitle("WinYandexMusicRPC - Console")
        self._disable_close_button()
        self._set_console_mode()
        self._check_conhost()
        self._check_run_by_startup()
        
        main_menu = self._build_tray_menu()
        icon_thread = threading.Thread(target=self._tray_thread, args=(main_menu,))
        icon_thread.daemon = True
        icon_thread.start()
    
    def _check_latest_version(self):
        try:
            import requests
            from packaging import version
            
            response = requests.get(
                f"{self.app_state.REPO_URL}/releases/latest", 
                timeout=5
            )
            response.raise_for_status()
            latest_version = response.url.split('/')[-1]
            
            if version.parse(self.app_state.CURRENT_VERSION) < version.parse(latest_version):
                log(
                    f"A new version has been released on GitHub. "
                    f"You are using - {self.app_state.CURRENT_VERSION}. "
                    f"A new version - {latest_version}, "
                    f"you can download it at {self.app_state.REPO_URL}/releases/tag/{latest_version}",
                    LogType.Notification
                )
            elif version.parse(self.app_state.CURRENT_VERSION) == version.parse(latest_version):
                log(f"You are using the latest version of the script")
            else:
                log(f"You are using the beta version of the script", LogType.Notification)
                
        except requests.exceptions.RequestException as e:
            log(f"Error getting latest version: {e}", LogType.Error)
    
    def _initialize_token(self, force_get=False):
        token = None
        
        if force_get:
            try:
                self._remove_token_from_memory()
                process = multiprocessing.Process(
                    target=self._update_token_task, 
                    args=(self._get_icon_path(), self.result_queue)
                )
                process.start()
                process.join()
                token = self.result_queue.get()
                
                if token and len(token) > 10:
                    import keyring
                    keyring.set_password('WinYandexMusicRPC', 'token', token)
                    log(f"Successfully received the token: {blur_string(token)}", LogType.Update_Status)
                    
            except Exception as e:
                log(f"Something happened when trying to initialize token: {e}", LogType.Error)
        else:
            if not self.app_state.ya_token:
                try:
                    import keyring
                    token = keyring.get_password('WinYandexMusicRPC', 'token')
                    if token:
                        log(f"Loaded token: {blur_string(token)}", LogType.Update_Status)
                except Exception as e:
                    log(f"Something happened when trying to initialize token: {e}", LogType.Error)
            else:
                token = self.app_state.ya_token
                log(f"Loaded token from script: {blur_string(token)}", LogType.Update_Status)
        
        if token and len(token) > 10:
            self.app_state.ya_token = token
            try:
                self.presence_service.initialize_client(token)
                account_name = self._get_account_name()
                log(f"Logged in as - {account_name}", LogType.Update_Status)
                if self._is_run_by_exe():
                    self._update_tray()
            except Exception as e:
                self._handle_yandex_exception(e)
        
        if not self.presence_service.client:
            log("Continue without a token...", LogType.Default)
    
    def _update_token_task(self, icon_path, result_queue):
        result = getToken.get_yandex_music_token(icon_path)
        result_queue.put(result)
    
    def _remove_token_from_memory(self):
        import keyring
        try:
            if keyring.get_password('WinYandexMusicRPC', 'token') is not None:
                keyring.delete_password('WinYandexMusicRPC', 'token')
                log("Old token has been removed from memory.", LogType.Update_Status)
        except Exception:
            pass
    
    def _get_account_name(self):
        try:
            user_info = self.presence_service.client.me.account
            return user_info.display_name or "None"
        except Exception:
            return "None"
    
    def _get_icon_path(self):
        try:
            if getattr(sys, 'frozen', False):
                resources_path = sys._MEIPASS
            else:
                resources_path = os.path.dirname(os.path.abspath(__file__))
            return f"{resources_path}/assets/YMRPC_ico.ico"
        except Exception:
            return None
    
    def _is_already_running(self):
        hwnd = win32gui.FindWindow(None, "WinYandexMusicRPC - Console")
        return bool(hwnd)
    
    def _show_console_permanent(self):
        try:
            win32gui.ShowWindow(self.window, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(self.window)
        except Exception as e:
            log(f"We cant show the window {e}", LogType.Error)
    
    def _wait_and_exit(self):
        self.presence_service.stop()
        input("Press Enter to close the program.\n")
        if self._is_run_by_exe():
            win32gui.PostMessage(self.window, win32con.WM_CLOSE, 0, 0)
        else:
            sys.exit(0)
    
    def _disable_close_button(self):
        hwnd = win32console.GetConsoleWindow()
        if hwnd:
            hMenu = win32gui.GetSystemMenu(hwnd, False)
            if hMenu:
                win32gui.DeleteMenu(hMenu, win32con.SC_CLOSE, win32con.MF_BYCOMMAND)
    
    def _set_console_mode(self):
        hStdin = win32console.GetStdHandle(win32console.STD_INPUT_HANDLE)
        mode = hStdin.GetConsoleMode()
        new_mode = mode & ~0x0040
        hStdin.SetConsoleMode(new_mode)
    
    def _check_conhost(self):
        if self._is_windows_11() and '--run-through-conhost' not in sys.argv:
            self._run_by_startup_without_conhost()
            print("Wait a few seconds for the script to load...")
            script_path = os.path.abspath(sys.argv[0])
            first_pid = os.getpid()
            subprocess.Popen(
                ['start', '/min', 'conhost.exe', script_path, '--run-through-conhost', str(first_pid)] + sys.argv[1:], 
                shell=True
            )
            event = threading.Event()
            event.wait()
        
        if '--run-through-launcher' in sys.argv or '--run-through-conhost' in sys.argv:
            if len(sys.argv) > 2:
                first_pid = int(sys.argv[2])
                try:
                    parent_process = psutil.Process(first_pid)
                    for child in parent_process.children(recursive=True):
                        child.terminate()
                    parent_process.terminate()
                    parent_process.wait(timeout=3)
                except Exception:
                    print(f"Couldnt close the process: {first_pid}")
    
    def _is_windows_11(self):
        return sys.getwindowsversion().build >= 22000
    
    def _run_by_startup_without_conhost(self):
        window = win32console.GetConsoleWindow()
        if window and '--run-through-startup' in sys.argv:
            win32gui.ShowWindow(window, win32con.SW_HIDE)
    
    def _check_run_by_startup(self):
        if self.window:
            if '--run-through-startup' not in sys.argv:
                self._show_console_permanent()
                log("Minimize to system tray in 3 seconds...")
                time.sleep(3)
            win32gui.ShowWindow(self.window, win32con.SW_HIDE)
        else:
            log("Console window not found", LogType.Error)
    
    def _build_tray_menu(self, icon=None):
        account_name = self._get_account_name()
        
        settings_menu = pystray.Menu(
            pystray.MenuItem(f"Logged in as - {account_name}", lambda: None, enabled=False),
            pystray.MenuItem('Login to account...', lambda: self._initialize_token(force_get=True)),
            pystray.MenuItem('Toggle strong_find', self._toggle_strong_find, checked=lambda item: self.app_state.strong_find),
        )
        
        return pystray.Menu(
            pystray.MenuItem("Hide/Show Console", self._toggle_console, default=True),
            pystray.MenuItem('Start with Windows', self._toggle_auto_start, checked=lambda item: self.app_state.auto_start_windows),
            pystray.MenuItem("Yandex settings", settings_menu),
            pystray.MenuItem("GitHub", self._tray_click),
            pystray.MenuItem("Exit", self._tray_click)
        )
    
    def _tray_thread(self, initial_menu):
        tray_image = Image.open(self._get_icon_path())
        icon = pystray.Icon("WinYandexMusicRPC", tray_image, "WinYandexMusicRPC", menu=initial_menu)
        self.icon_tray = icon
        icon.run_detached()
        self._update_tray()
    
    def _update_tray(self):
        if self.icon_tray is not None:
            self.icon_tray.menu = self._build_tray_menu(self.icon_tray)
    
    def _toggle_console(self):
        if win32gui.IsWindowVisible(self.window):
            win32gui.ShowWindow(self.window, win32con.SW_HIDE)
        else:
            self._show_console_permanent()
    
    def _toggle_strong_find(self):
        self.app_state.strong_find = not self.app_state.strong_find
        self.config_manager.set_setting('UserSettings', 'strong_find', str(self.app_state.strong_find))
        log(f'Bool strong_find set state: {self.app_state.strong_find}')
    
    def _toggle_auto_start(self):
        self.app_state.auto_start_windows = not self.app_state.auto_start_windows
        log(f'Bool auto_start_windows set state: {self.app_state.auto_start_windows}')
        
        def change_setting(toggle):
            if toggle:
                try:
                    exe_path = os.path.abspath(sys.argv[0])
                    shortcut_path = os.path.join(
                        os.getenv('APPDATA'), 'Microsoft', 'Windows', 
                        'Start Menu', 'Programs', 'Startup', 'YaMusicRPC.lnk'
                    )
                    self._create_shortcut(exe_path, shortcut_path, arguments="--run-through-startup")
                except:
                    exe_path = f'"{os.path.abspath(sys.argv[0])}" --run-through-startup'
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER, 
                        r'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run', 
                        0, winreg.KEY_SET_VALUE
                    )
                    winreg.SetValueEx(key, 'YaMusicRPC', 0, winreg.REG_SZ, exe_path)
                    winreg.CloseKey(key)
            else:
                shortcut_path = os.path.join(
                    os.getenv('APPDATA'), 'Microsoft', 'Windows', 
                    'Start Menu', 'Programs', 'Startup', 'YaMusicRPC.lnk'
                )
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER, 
                        r'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run', 
                        0, winreg.KEY_ALL_ACCESS
                    )
                    winreg.DeleteValue(key, 'YaMusicRPC')
                    winreg.CloseKey(key)
                except FileNotFoundError:
                    pass
        
        threading.Thread(target=change_setting, args=[self.app_state.auto_start_windows]).start()
    
    def _create_shortcut(self, target, shortcut_path, description="", arguments=""):
        import pythoncom
        pythoncom.CoInitialize()
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortcut(shortcut_path)
        shortcut.TargetPath = target
        shortcut.WorkingDirectory = os.path.dirname(target)
        shortcut.Description = description
        shortcut.Arguments = arguments
        shortcut.Save()
    
    def _tray_click(self, icon, query):
        if str(query) == "GitHub":
            webbrowser.open(self.app_state.REPO_URL, new=2)
        elif str(query) == "Exit":
            self.presence_service.stop()
            icon.stop()
            win32gui.PostMessage(self.window, win32con.WM_CLOSE, 0, 0)
    
    def _handle_yandex_exception(self, exception):
        json_str = str(exception).replace("'", '"')
        match = re.search(r'({.*?})', json_str)
        
        if match:
            json_str = match.group(1)
        
        try:
            data = json.loads(json_str)
            error_name = data.get('name')
            
            if error_name == 'Unavailable For Legal Reasons':
                log(
                    "You are using Yandex music in a country where it is not available "
                    "without authorization! Turn off VPN or login using a Yandex token.",
                    LogType.Error
                )
            elif error_name == 'session-expired':
                log("Your Yandex token is out of date or incorrect, login again.", LogType.Error)
            else:
                log(f"Something happened: {exception}", LogType.Error)
        except Exception:
            log(f"Something happened: {exception}", LogType.Error)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    app = Application()
    app.run()
