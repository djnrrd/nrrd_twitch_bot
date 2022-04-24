from logging import Logger
from aiohttp import web


async def _handler(request):
    return web.Response(text="OK")


async def main(logger: Logger) -> web.TCPSite:
    """Start a simple aiohttp server and return it

    :param logger: A logger object
    :return: The web server for shutting down externally
    """
    app = web.Application()
    app.add_routes([web.get('/', _handler)])
    runner = web.AppRunner(app)
    await runner.setup()
    logger.info('Starting local HTTP Server')
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    return site
