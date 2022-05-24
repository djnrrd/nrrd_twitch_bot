"""Run the main web server and websocket components as asyncio tasks
"""
from typing import List, Union, Type
from logging import Logger
import asyncio
import signal
import threading
from functools import partial
from asyncio import PriorityQueue, Event
from nrrd_twitch_bot.lib.twitch_chat import TwitchChat
from nrrd_twitch_bot.lib.config import load_default_config
from nrrd_twitch_bot.lib.dispatcher import Dispatcher
from nrrd_twitch_bot.lib.plugins import load_plugins, BasePlugin
from nrrd_twitch_bot.lib.http_server import OverlayServer


def start_new_thread(logger: Logger, shutdown_event: Event) -> None:
    """Create a new thread to run the asyncio tasks in

    :param logger: A Logger object
    :param shutdown_event: An asyncio event to trigger shutting down the
        services
    """
    start_services = partial(run_async_tasks, logger, shutdown_event)
    logger.debug('run.py: Starting thread for websockets')
    services = threading.Thread(target=start_services, daemon=True)
    services.start()


async def run_chat(chat_rcv_queue: PriorityQueue,
                   chat_send_queue: PriorityQueue,
                   logger: Logger) -> None:
    """Run the Twitch chat service as an asyncio task

    :param chat_rcv_queue: The queue for passing messages received from
        twitch chat to the dispatcher
    :param chat_send_queue: The queue for passing messages back to twitch chat
    :param logger: A logger object
    """
    config = load_default_config(logger)
    oauth_token = config['twitch']['oauth_token']
    nickname = config['twitch']['username']
    channel = config['twitch']['channel']
    logger.info('run.py: Starting twitch chat service')
    async with TwitchChat(oauth_token, nickname, channel, chat_rcv_queue,
                          chat_send_queue, logger) as chat:
        await chat.run()


async def run_dispatcher(chat_rcv_queue: PriorityQueue,
                         chat_send_queue: PriorityQueue,
                         plugins: List[BasePlugin],
                         logger: Logger) -> None:
    """Run the dispatcher service as an asyncio task

    :param chat_rcv_queue: The queue for passing messages received from
        twitch chat to the dispatcher
    :param chat_send_queue: The queue for passing messages back to twitch chat
    :param plugins: A list of plugin objects
    :param logger: A logger object
    """
    dispatcher = Dispatcher(chat_rcv_queue, chat_send_queue, plugins, logger)
    logger.debug('run.py: running dispatcher')
    await dispatcher.run()


async def run_http(plugins: List[BasePlugin], logger: Logger) -> None:
    """Run the HTTP server

    :param plugins: A list of plugin objects
    :param logger: A logger object
    """
    async with OverlayServer(plugins, logger) as http:
        logger.debug('run.py: running http server')
        await http.run()


async def run_plugins(plugin: Type[BasePlugin], logger: Logger) -> None:
    """Run any plugins that implement the run() method

    :param plugin: The plugin object
    :param logger:
    """
    if hasattr(plugin, 'run'):
        logger.debug(f"run.py: running plugin {plugin}")
        await plugin.run()


async def shutdown(loop: asyncio.AbstractEventLoop, logger: Logger) \
        -> None:
    """Gracefully Shutdown the services

    :param loop: The asyncio event loop
    :param logger: A logger object
    """
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    logger.debug(f"run.py: Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


async def shutdown_on_event(shutdown_event: Event,
                            loop: asyncio.AbstractEventLoop,
                            logger: Logger) -> None:
    """Listen for an asyncio event from the TK app to trigger a shutdown

    :param shutdown_event: The asyncio Event
    :param loop: The asyncio event loop
    :param logger: A logger object
    """
    await shutdown_event.wait()
    logger.debug('run.py: Shutdown event received')
    await shutdown(loop, logger)
    shutdown_event.clear()


def register_signal_handlers(loop: asyncio.AbstractEventLoop,
                             logger: Logger) -> None:
    """Register shutdown signals and the shutdown handlers to the event loop

    :param loop: The asyncio event loop
    :param logger: A logger object
    """
    # Register the signal handlers
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for sig in signals:
        logger.debug(f"run.py: Adding handler for signal {sig}")
        loop.add_signal_handler(
            sig, lambda: asyncio.create_task(shutdown(loop, logger))
        )


def run_async_tasks(logger: Logger, shutdown_event: Union[Event, None] = None) \
        -> None:
    """Start all the services as asyncio tasks and run the event loop

    :param logger: A logger object
    :param shutdown_event: An asyncio Event object used by the main TK thread
        to signal a shutdown of the event loop
    """
    # Setup async queues
    chat_rcv_queue = PriorityQueue()
    chat_send_queue = PriorityQueue()
    # Gather the plugins
    plugins = load_plugins(logger)
    # Get the loop
    loop = asyncio.new_event_loop()
    try:
        loop.create_task(run_chat(chat_rcv_queue, chat_send_queue, logger))
        loop.create_task(run_dispatcher(chat_rcv_queue, chat_send_queue,
                                        plugins, logger))
        loop.create_task(run_http(plugins, logger))
        if shutdown_event:
            loop.create_task(shutdown_on_event(shutdown_event, loop, logger))
        else:
            register_signal_handlers(loop, logger)
        for plugin in plugins:
            loop.create_task(run_plugins(plugin, logger))
        loop.run_forever()
    finally:
        loop.close()
