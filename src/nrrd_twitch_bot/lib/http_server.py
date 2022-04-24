"""Module for managing a local HTTP server for OBS overlays
"""
from typing import List
from logging import Logger
from aiohttp import web
from .plugins import load_overlays


def route_plugins(logger: Logger) -> List[web.RouteDef]:
    plugins = load_overlays(logger)
    # Use the plugin package name as the path
    return [web.get(f"/{x.__name__.split('.')[0]}/{{path:.*}}", x.handler)
            for x in plugins]


async def main(logger: Logger) -> web.TCPSite:
    """Start a simple aiohttp server and return it

    :param logger: A logger object
    :return: The web server for shutting down externally
    """
    app = web.Application()
    plugin_routes = route_plugins(logger)
    app.add_routes(plugin_routes)
    runner = web.AppRunner(app)
    await runner.setup()
    logger.info('Starting local HTTP Server')
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    return site
