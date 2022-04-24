"""chat overlay plugin dispatcher module
"""
from typing import Dict
from logging import Logger
from asyncio import PriorityQueue
from nrrd_twitch_bot import Dispatcher


@Dispatcher.do_privmsg
async def do_privmsg(msg: Dict, send_queue: PriorityQueue, logger: Logger) \
        -> None:
    """Log the message dictionary from the dispatcher to the logger object

    :param msg: Websockets privmsg dictionary, with all tags as Key/Value
        pairs, plus the 'nickname' key, and the 'msg_text' key
    :param send_queue: The queue object to send messages back to TwitchChat
    :param logger: A Logger object
    """
    logger.debug(f"chat_overlay plugin: {msg}")
