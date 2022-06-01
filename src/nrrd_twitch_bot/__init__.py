"""A twitch bot using a plugin based architecture
"""
from .lib.dispatcher import Dispatcher
from .lib.plugins import BasePlugin
from .lib.config import load_config, save_config
from .lib.twitch_helix import get_channel_badges
