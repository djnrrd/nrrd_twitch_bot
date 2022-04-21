"""Run the main web server and websocket components in their threads
"""
import threading
from functools import partial
from logging import Logger
import asyncio
from .twitch_chat import TwitchChat
from .config import load_config


async def message_handler(chat: TwitchChat, logger: Logger,
                          loop: asyncio.AbstractEventLoop,
                          message_queue: asyncio.Queue, ) -> None:
    """Read the Queue for messages and route them to the appropriate objects

    :param chat: The TwitchChat object
    :param logger: A logger object
    :param loop: The asyncio event loop
    :param message_queue: A python queue object
    """
    logger.debug('Starting message handler')
    q_loop = True
    while q_loop:
        message = await message_queue.get()
        if message == 'SHUTDOWN':
            logger.debug('Shutdown message received')
            loop.call_soon(asyncio.create_task, chat.close())
            message_queue.task_done()
            q_loop = False
    logger.debug('Exiting message handler')


async def async_twitch_chat_main(oauth_token: str, nickname: str, channel: str,
                                 logger: Logger,
                                 loop: asyncio.AbstractEventLoop,
                                 message_queue: asyncio.Queue,) -> None:
    """Run the Twitch Chat websockets client

    :param oauth_token: The OAuth token to log into Twitch
    :param nickname: The twitch nickname to log in as
    :param channel: The twitch channel to join
    :param logger: A logger object
    :param loop: The asyncio event loop
    :param message_queue: A python asyncio Queue object
    """
    async with TwitchChat(oauth_token, nickname, channel, logger) as chat:
        logger.debug('Using asyncio gather to run chatbot and queue manager')
        futures = [chat.run(),
                   message_handler(chat, logger, loop, message_queue)]
        await asyncio.gather(*futures)
    logger.debug('Exiting TwitchChat and message handler')


def twitch_chat_main(logger: Logger, loop: asyncio.AbstractEventLoop,
                     message_queue: asyncio.Queue) -> None:
    """Start the Twitch chat websockets client in an asyncio loop

    :param logger: A Logger object
    :param loop: The asyncio event loop
    :param message_queue: A python asyncio Queue object
    """
    config = load_config(logger)
    logger.debug('Starting loop')
    loop.run_until_complete(
        async_twitch_chat_main(config['twitch']['oauth_token'],
                               config['twitch']['username'],
                               config['twitch']['channel'],
                               logger, loop, message_queue)
    )
    logger.debug('Ending loop')


def run_threads(logger: Logger, loop: asyncio.AbstractEventLoop,
                message_queue: asyncio.Queue) -> None:
    """Create the threads and queues to run the websocket clients and servers
    in

    :param logger: A Logger object
    :param loop: The asyncio event loop
    :param message_queue: A python asyncio Queue object
    """
    start_chat = partial(twitch_chat_main, logger, loop, message_queue)
    logger.debug('Starting thread for websockets')
    chat = threading.Thread(target=start_chat, daemon=True)
    chat.start()

