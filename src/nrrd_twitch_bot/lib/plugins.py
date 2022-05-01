"""Load plugins from the config file and import them
"""
from typing import List
from asyncio import PriorityQueue, create_task
from logging import Logger
from aiohttp.web import Request, WebSocketResponse
from inspect import getmembers, isclass
import os
import sys
import importlib
import importlib.util
from appdirs import user_data_dir
from .config import load_config


class BasePlugin:
    """Basic object that plugins must inherit from, providing a logger and
    queues

    :param send_chat_queue: The asyncio queue object for sending to chat
    :param logger: A logger object
    """
    def __init__(self, send_chat_queue: PriorityQueue, logger: Logger) -> None:
        self.send_chat_queue = send_chat_queue
        self.websocket_queue = PriorityQueue()
        self.logger = logger

    async def send_chat(self, message: str) -> None:
        """Send a chat message back to the dispatcher

        :param message: The text to send to chat
        """
        await self.send_chat_queue.put(message)

    async def _websocket_handler(self, request: Request) -> WebSocketResponse:
        """A websocket handler to send messages to Overlays

                :param request: An aiohttp Request object
                :return: The WebSocket response
                """
        ws = WebSocketResponse()
        await ws.prepare(request)
        # Add the websocket to the application registry
        request.app['websockets'].add(ws)
        task = create_task(self._send_from_queue(ws))
        try:
            async for msg in ws:
                pass
        finally:
            request.app['websockets'].discard(ws)
            task.cancel()
        return ws

    async def _send_from_queue(self, ws):
        while not ws.closed:
            message = await self.websocket_queue.get()
            await ws.send_str(message)
            self.websocket_queue.task_done()


def _load_from_config(logger: Logger) -> List[str]:
    """Load the list of plugin names from the config file

    :param logger: A logger object
    :return: The list of plugin names
    """
    logger.debug('plugins.py: Loading plugin list')
    config = load_config(logger)
    plugins = config['plugins']['plugins']
    logger.debug(f"plugins.py: plugins list: {plugins}")
    return plugins.split(':')


def _update_paths(logger: Logger) -> None:
    """Update the sys path with the plugin locations

    :param logger:
    """
    logger.debug('plugins.py: Adding local plugin path')
    local_plugin_path = os.path.join(os.path.dirname(__file__), '..', 'plugins')
    user_plugin_path = os.path.join(user_data_dir('nrrd-twitch-bot', 'djnrrd'),
                                    'plugins')
    if not os.path.isdir(user_plugin_path):
        logger.debug('plugins.py: No plugin directory found, creating one')
        # On Windows appdirs always have to be %AppDir%//author//appname so
        # we have to create the author folder first, which would end up being
        # empty on linux systems
        author_dir = os.path.join(user_data_dir(), 'djnrrd')
        if not os.path.isdir(author_dir):
            logger.debug(f"plugins.py: Creating author directory: {author_dir}")
            os.mkdir(author_dir)
        app_dir = user_data_dir('nrrd-twitch-bot', 'djnrrd')
        if not os.path.isdir(app_dir):
            logger.debug(f"plugins.py: Creating application directory: "
                         f"{app_dir}")
            os.mkdir(app_dir)
        logger.debug(f"plugins.py: Creating plugin directory: "
                     f"{user_plugin_path}")
        os.mkdir(user_plugin_path)
    sys.path.extend([local_plugin_path, user_plugin_path])


def load_plugins(send_queue: PriorityQueue, logger: Logger) -> List[BasePlugin]:
    """load all plugin objects

    :param send_queue: An asyncio priority queue object
    :param logger: A logger object
    :return: A list of initiated of plugins
    """
    _update_paths(logger)
    modules = _load_from_config(logger)
    logger.info('plugins.py: Importing plugin libraries')
    plugins = []
    for module in modules:
        if importlib.util.find_spec('.plugin', module):
            load_module = importlib.import_module('.plugin', module)
            logger.debug(f"plugins.py: Imported {str(load_module)} "
                         f"from {module}")
            for cls in getmembers(load_module, isclass):
                if cls[1].__module__ == load_module.__name__:
                    logger.debug(f"Initialising plugin {cls[0]} "
                                 f"from {load_module}")
                    plugins.append(cls[1](send_queue, logger))
    return plugins
