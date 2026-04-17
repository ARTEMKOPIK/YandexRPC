"""
Discord Rich Presence manager module.
Handles connection and updates to Discord RPC.
"""

import time
import psutil
import pypresence

from .app_state import get_app_state, ActivityTypeConfig, LanguageConfig, LogType
from .exceptions import DiscordRPCError
from ..utils.logger import log


class DiscordRPCManager:
    """
    Manages Discord Rich Presence connection and updates.
    Encapsulates all RPC-related functionality.
    """
    
    EXE_NAMES = ["Discord.exe", "DiscordCanary.exe", "DiscordPTB.exe", "Vesktop.exe"]
    
    def __init__(self):
        self.rpc = None
        self.running = False
        self.paused = False
        self._app_state = get_app_state()
    
    @classmethod
    def is_discord_running(cls):
        """Check if any Discord client is running."""
        return any(
            name in (p.name() for p in psutil.process_iter()) 
            for name in cls.EXE_NAMES
        )
    
    def connect(self):
        """
        Connect to Discord RPC.
        
        Returns:
            pypresence.Presence instance or None if connection fails
        """
        try:
            client_id = self._app_state.get_client_id()
            rpc = pypresence.Presence(client_id)
            rpc.connect()
            return rpc
        except pypresence.exceptions.DiscordNotFound:
            log("Pypresence - Discord not found.", LogType.Error)
            return None
        except pypresence.exceptions.InvalidID:
            log("Pypresence - Incorrect CLIENT_ID", LogType.Error)
            return None
        except Exception as e:
            log(f"Discord is not ready for a reason: {e}", LogType.Error)
            return None
    
    def wait_for_discord(self):
        """Wait until Discord is available and connected."""
        while True:
            if self.is_discord_running():
                self.rpc = self.connect()
                if self.rpc:
                    log("Discord is ready for Rich Presence")
                    break
                else:
                    log(
                        "Discord is launched but not ready for Rich Presence. Try again...",
                        LogType.Error
                    )
            else:
                log("Discord is not launched", LogType.Error)
            time.sleep(3)
    
    def stop(self):
        """Stop Discord RPC and clean up."""
        if self.rpc:
            self.rpc.close()
            self.rpc = None
            self.running = False
    
    def restart(self):
        """Restart Discord RPC connection."""
        self._app_state.reset_track_state()
        
        if self.rpc:
            self.rpc.close()
            self.rpc = None
        
        time.sleep(3)
        self.wait_for_discord()
    
    def handle_disconnect(self):
        """Handle Discord disconnection."""
        log("Discord was closed. Waiting for restart...", LogType.Error)
        self._app_state.reset_track_state()
        self.wait_for_discord()
    
    def update_presence(self, **kwargs):
        """
        Update Discord presence with given parameters.
        
        Args:
            **kwargs: Arguments to pass to rpc.update()
        """
        if self.rpc:
            self.rpc.update(**kwargs)
    
    def clear_presence(self):
        """Clear Discord presence."""
        if self.rpc:
            self.rpc.clear()
            log("Clear RPC", LogType.Update_Status)
