"""Load plugins from the config file and import them
"""
from typing import List, Dict, Union, TYPE_CHECKING
from asyncio import PriorityQueue, create_task
from logging import Logger
from inspect import getmembers, isclass
import os
import sys
import json
import importlib
import importlib.util
from aiohttp.web import Request, WebSocketResponse
from appdirs import user_data_dir
from .config import load_config
if TYPE_CHECKING:
    from .dispatcher import Dispatcher


class BasePlugin:
    """Basic object that plugins must inherit from, providing a logger and
    queues

    :param logger: A logger object
    """
    def __init__(self, logger: Logger) -> None:
        self.websocket_queue: PriorityQueue = PriorityQueue()
        self.dispatcher: Union[Dispatcher, None] = None
        self.logger = logger

    async def send_web_socket(self, message: Union[List, Dict, str, bytes]):
        """Send a message to the Websockets server for overlays

        :param message: The message to send to the websockets
        """
        # If multiple messages are in the queue with the same priority,
        # the values are compared, which cannot be done with dict objects,
        # so do a conversion to a JSON string here.
        if isinstance(message, (list, dict)):
            message = json.dumps(message)
        await self.websocket_queue.put((0, message))

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
                # OBS overlays would not be expected to send info back,
                # but we need to run this loop to handle PING messages from
                # the client
                pass
        finally:
            request.app['websockets'].discard(ws)
            task.cancel()
        return ws

    async def _send_from_queue(self, ws: WebSocketResponse) -> None:
        """Send a frame to the websockets server

        :param ws: The WebSocketResponse object
        """
        while not ws.closed:
            message = await self.websocket_queue.get()
            if isinstance(message[1], str):
                await ws.send_str(message[1])
            else:
                await ws.send_bytes(message[1])
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


def load_plugins(logger: Logger) -> List[BasePlugin]:
    """load all plugin objects

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
                    logger.debug(f"plugins.py: Initialising plugin {cls[0]} "
                                 f"from {load_module}")
                    plugins.append(cls[1](logger))
    return plugins
