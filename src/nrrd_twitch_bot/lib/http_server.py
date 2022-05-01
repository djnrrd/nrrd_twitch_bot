"""Module for managing a local HTTP server for OBS overlays
"""
from typing import List
from logging import Logger
from aiohttp import web, WSCloseCode
import weakref
from nrrd_twitch_bot.lib.plugins import BasePlugin


def route_plugins(plugins: List[BasePlugin], logger: Logger) \
        -> List[web.RouteDef]:
    """Create the routes

    :param plugins: A list of plugins
    :param logger: A logger object
    :return:
    """
    ret_list = []
    for plugin in plugins:
        # Use the plugin package name as the path
        package = plugin.__module__.split('.')[0]
        if hasattr(plugin, 'http_handler'):
            logger.debug(f"http_server.py: Adding route for package {package} "
                         f"to HTTP server")
            ret_list.append(web.get(f"/{package}/http/{{path:.*}}",
                                    plugin.http_handler))
        if hasattr(plugin, 'websocket_handler'):
            logger.debug(f"http_server.py: Adding route for package {package} "
                         f"to WebSockets server")
            ret_list.append(web.get(f"/{package}/ws/",
                                    plugin.websocket_handler))
    return ret_list


async def on_shutdown(app: web.Application) -> None:
    """Gracefully shutdown websocket sessions

    :param app: The aiohttp web application
    """
    for ws in set(app['websockets']):
        await ws.close(code=WSCloseCode.GOING_AWAY,
                       message='Server shutdown')


async def run_http_server(plugins: List[BasePlugin], logger: Logger) \
        -> web.TCPSite:
    """Start a simple aiohttp server and return it

    :param plugins: A list of plugins
    :param logger: A logger object
    :return: The web server for shutting down externally
    """
    app = web.Application()
    # Prepare a registry for the websocket sessions
    app['websockets'] = weakref.WeakSet()
    app.on_shutdown.append(on_shutdown)
    plugin_routes = route_plugins(plugins, logger)
    app.add_routes(plugin_routes)
    runner = web.AppRunner(app)
    await runner.setup()
    logger.info('http_server.py: Starting local HTTP Server')
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    return site
