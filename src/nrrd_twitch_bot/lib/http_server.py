"""Module for managing a local HTTP server for OBS overlays
"""
from typing import List, Optional, Type, Union
from types import TracebackType
from logging import Logger
import asyncio
import weakref
from aiohttp import web, WSCloseCode
from nrrd_twitch_bot.lib.plugins import BasePlugin


class OverlayServer:
    """Wrap the aiohttp server in a class that can be used as a context
    manager

    :param plugins: A list of plugins that may be added to the web server
    :param logger: A logger object
    """
    def __init__(self, plugins: List[BasePlugin], logger: Logger) -> None:
        self.logger = logger
        self.routes = self._build_routes(plugins)
        self.site: Union[web.TCPSite, None] = None

    def __enter__(self) -> None:
        """Should not be using with the normal context manager"""
        raise TypeError("Use async with instead")

    def __exit__(self,
                 exc_type: Optional[Type[BaseException]],
                 exc_val: Optional[BaseException],
                 exc_tb: Optional[TracebackType]) -> None:
        """This should never be called but is required for the normal context
        manager"""
        pass

    async def __aenter__(self) -> 'OverlayServer':
        """Entry point for the async context manager"""
        await self.open()
        return self

    async def __aexit__(self,
                        exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]) -> None:
        """Exit point for the async context manager"""
        await self.close()

    async def open(self) -> None:
        """Build the HTTP server and start to run it
        """
        if not self.site:
            runner = await self._build_runner()
            self.site = web.TCPSite(runner, 'localhost', 8080)
            self.logger.info('http_server.py: Starting HTTP Server')
            await self.site.start()

    async def close(self) -> None:
        """Use the TCPSite functionality to gracefully shut down the HTTP server
        """
        if self.site:
            self.logger.info('http_server.py: Shutting down HTTP server')
            await self.site.stop()

    def _build_routes(self, plugins: List[BasePlugin]) -> List[web.RouteDef]:
        """Create the list of routes

        :param plugins: A list of plugins
        :return: A list of aiohttp route objects
        """
        ret_list = []
        for plugin in plugins:
            # Use the plugin package name as the path
            package = plugin.__module__.split('.')[0]
            if hasattr(plugin, 'http_handler'):
                self.logger.debug(f"http_server.py: Adding route for "
                                  f"package {package} to HTTP server")
                ret_list.append(web.get(f"/{package}/http/{{path:.*}}",
                                        plugin.http_handler))
            if hasattr(plugin, 'websocket_handler'):
                self.logger.debug(f"http_server.py: Adding route for "
                                  f"package {package} to WebSockets server")
                ret_list.append(web.get(f"/{package}/ws/",
                                        plugin.websocket_handler))
        return ret_list

    async def _build_runner(self) -> web.AppRunner:
        """Build the aiohttp application and web runner

        :return: The aiohttp AppRunner object
        """
        self.logger.debug('http_server.py: Building AppRunner and routes')
        app = web.Application()
        # Prepare a registry for the websocket sessions
        app['websockets'] = weakref.WeakSet()
        app['logger'] = self.logger
        app.on_shutdown.append(OverlayServer.on_shutdown)
        app.add_routes(self.routes)
        runner = web.AppRunner(app)
        await runner.setup()
        return runner

    @staticmethod
    async def on_shutdown(app: web.Application) -> None:
        """Gracefully shutdown websocket sessions

        :param app: The aiohttp web application
        """
        app['logger'].debug(f"http_server.py: {set(app['websockets'])}")
        for ws in set(app['websockets']):
            app['logger'].debug(f"http_server.py: shutting down websocket {ws}")
            await ws.close(code=WSCloseCode.GOING_AWAY,
                           message='Server shutdown')

    @staticmethod
    async def run() -> None:
        """Dummy function to keep the context manager open
        """
        while True:
            await asyncio.sleep(0)
