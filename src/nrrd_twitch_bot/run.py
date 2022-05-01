"""Run the main web server and websocket components in their threads
"""
import threading
from functools import partial
from logging import Logger
from aiohttp.web import TCPSite
import asyncio
from nrrd_twitch_bot.lib.twitch_chat import TwitchChat
from nrrd_twitch_bot.lib.config import load_config
from nrrd_twitch_bot.lib.dispatcher import Dispatcher
from nrrd_twitch_bot.lib.plugins import load_plugins
from nrrd_twitch_bot.lib.http_server import run_http_server


async def shutdown_handler(chat: TwitchChat, dispatcher: Dispatcher,
                           site: TCPSite, logger: Logger,
                           loop: asyncio.AbstractEventLoop,
                           shutdown_queue: asyncio.PriorityQueue) -> None:
    """Read the Shutdown Queue waiting for the shutdown message and shutdown
    the asyncio operations

    :param chat: The TwitchChat object
    :param dispatcher: The BotDispatcher object
    :param site: The local HTTP Server
    :param logger: A logger object
    :param loop: The asyncio event loop
    :param shutdown_queue: A python queue object for handling shutdowns from
        the TK thread
    """
    logger.debug('run.py: Starting shutdown handler')
    q_loop = True
    while q_loop:
        message = await shutdown_queue.get()
        if message[1] == 'SHUTDOWN':
            logger.debug('run.py: Shutdown message received')
            logger.debug('run.py: Shutting down local HTTP Server')
            await site.stop()
            logger.debug('run.py: Shutting down dispatcher')
            loop.call_soon(asyncio.create_task, dispatcher.shutdown())
            logger.debug('run.py: Shutting down chat')
            loop.call_soon(asyncio.create_task, chat.close())
            q_loop = False
        shutdown_queue.task_done()
    logger.debug('run.py: Exiting shutdown handler')


async def async_main(oauth_token: str, nickname: str, channel: str,
                     logger: Logger,
                     loop: asyncio.AbstractEventLoop,
                     shutdown_queue: asyncio.PriorityQueue) -> None:
    """Run the asyncio tasks in parallel

    :param oauth_token: The OAuth token to log into Twitch chat
    :param nickname: The twitch nickname to log into Twitch chat as
    :param channel: The twitch channel to join for to Twitch chat
    :param logger: A logger object
    :param loop: The asyncio event loop
    :param shutdown_queue: A python queue object receiving shutdowns from
        the main TK thread
    """
    # Setup other async queues
    chat_rcv_queue = asyncio.PriorityQueue()
    chat_send_queue = asyncio.PriorityQueue()
    # Load twitch chat web sockets client and open the connection
    logger.debug('run.py: Loading TwitchChat')
    chat = TwitchChat(oauth_token, nickname, channel, logger, chat_rcv_queue)
    await chat.open()
    # Gather the plugins
    logger.debug('run.py: Loading plugins')
    plugins = load_plugins(chat_send_queue, logger)
    # Initialise the dispatcher
    logger.debug('run.py: Loading Dispatcher')
    dispatcher = Dispatcher(chat, chat_rcv_queue, chat_send_queue,
                            plugins, logger)
    # Initialise the HTTP server
    logger.debug('run.py: Starting aiohttp server')
    http_site = await run_http_server(plugins, logger)
    logger.debug('run.py: Using asyncio gather to run chat, dispatcher and '
                 'shutdown handler')
    futures = [chat.run(),
               dispatcher.chat_receive(),
               dispatcher.chat_send(),
               shutdown_handler(chat, dispatcher, http_site, logger, loop,
                                shutdown_queue)]
    await asyncio.gather(*futures)
    logger.debug('run.py: All asyncio tasks')


def start_asyncio_loop(logger: Logger, loop: asyncio.AbstractEventLoop,
                       shutdown_queue: asyncio.PriorityQueue) -> None:
    """Start the asyncio event loop

    :param logger: A Logger object
    :param loop: The asyncio event loop
    :param shutdown_queue: A python queue object for handling shutdowns from
        the TK thread
    """
    config = load_config(logger)
    oauth = config['twitch']['oauth_token']
    username = config['twitch']['username']
    channel = config['twitch']['channel']
    logger.debug('run.py: Starting asyncio event loop')
    loop.run_until_complete(
        async_main(oauth, username, channel, logger, loop, shutdown_queue)
    )
    logger.debug('run.py: Ending asyncio event loop')


def start_new_thread(logger: Logger, loop: asyncio.AbstractEventLoop,
                     shutdown_queue: asyncio.PriorityQueue) -> None:
    """Create a new thread to run the asyncio tasks in

    :param logger: A Logger object
    :param loop: The asyncio event loop
    :param shutdown_queue: A python queue object for handling shutdowns from
        the TK thread
    """
    start_chat = partial(start_asyncio_loop, logger, loop, shutdown_queue)
    logger.debug('run.py: Starting thread for websockets')
    chat = threading.Thread(target=start_chat, daemon=True)
    chat.start()
