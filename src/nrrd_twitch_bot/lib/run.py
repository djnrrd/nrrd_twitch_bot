"""Run the main web server and websocket components in their threads
"""
import threading
from functools import partial
from logging import Logger
import asyncio
from .twitch_chat import TwitchChat
from .config import load_config
from .dispatcher import BotDispatcher


async def shutdown_handler(chat: TwitchChat, dispatcher: BotDispatcher,
                           logger: Logger,
                           loop: asyncio.AbstractEventLoop,
                           shutdown_queue: asyncio.Queue, ) -> None:
    """Read the Queue for messages and route them to the appropriate objects

    :param chat: The TwitchChat object
    :param dispatcher: The BotDispatcher object
    :param logger: A logger object
    :param loop: The asyncio event loop
    :param shutdown_queue: A python queue object for handling shutdowns from
        the TK thread
    """
    logger.debug('Starting message handler')
    q_loop = True
    while q_loop:
        message = await shutdown_queue.get()
        if message == 'SHUTDOWN':
            logger.debug('Shutdown handler message received')
            loop.call_soon(asyncio.create_task, dispatcher.shutdown())
            loop.call_soon(asyncio.create_task, chat.close())
            q_loop = False
        shutdown_queue.task_done()
    logger.debug('Exiting message handler')


async def async_twitch_chat_main(oauth_token: str, nickname: str, channel: str,
                                 logger: Logger,
                                 loop: asyncio.AbstractEventLoop,
                                 shutdown_queue: asyncio.Queue) -> None:
    """Run the Twitch Chat websockets client

    :param oauth_token: The OAuth token to log into Twitch
    :param nickname: The twitch nickname to log in as
    :param channel: The twitch channel to join
    :param logger: A logger object
    :param loop: The asyncio event loop
    :param shutdown_queue: A python queue object for handling shutdowns from
        the TK thread
    """
    chat_rcv_queue = asyncio.PriorityQueue()
    chat_send_queue = asyncio.PriorityQueue()
    chat = TwitchChat(oauth_token, nickname, channel, logger, chat_rcv_queue)
    await chat.open()
    dispatcher = BotDispatcher(chat, chat_rcv_queue, chat_send_queue, logger)
    logger.debug('Using asyncio gather to run chatbot and queue manager')
    futures = [chat.run(),
               dispatcher.chat_receive(),
               dispatcher.chat_send(),
               shutdown_handler(chat, dispatcher, logger, loop, shutdown_queue)]
    await asyncio.gather(*futures)
    logger.debug('Exiting TwitchChat and message handler')


def twitch_chat_main(logger: Logger, loop: asyncio.AbstractEventLoop,
                     shutdown_queue: asyncio.Queue) -> None:
    """Start the Twitch chat websockets client in an asyncio loop

    :param logger: A Logger object
    :param loop: The asyncio event loop
    :param shutdown_queue: A python queue object for handling shutdowns from
        the TK thread
    """
    config = load_config(logger)
    logger.debug('Starting loop')
    loop.run_until_complete(
        async_twitch_chat_main(config['twitch']['oauth_token'],
                               config['twitch']['username'],
                               config['twitch']['channel'],
                               logger, loop, shutdown_queue)
    )
    logger.debug('Ending loop')


def run_sockets(logger: Logger, loop: asyncio.AbstractEventLoop,
                shutdown_queue: asyncio.Queue) -> None:
    """Create the threads to run the websocket clients and servers in

    :param logger: A Logger object
    :param loop: The asyncio event loop
    :param shutdown_queue: A python queue object for handling shutdowns from
        the TK thread
    """
    start_chat = partial(twitch_chat_main, logger, loop, shutdown_queue)
    logger.debug('Starting thread for websockets')
    chat = threading.Thread(target=start_chat, daemon=True)
    chat.start()
