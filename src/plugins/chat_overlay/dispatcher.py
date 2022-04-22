from typing import Dict
from logging import Logger
from lib.dispatcher import BotDispatcher


@BotDispatcher.do_privmsg
async def do_privmsg(msg: Dict, logger: Logger) -> None:
    """Log the message dictionary from the dispatcher to the logger object

    :param msg: Websockets privmsg dictionary, with all tags as Key/Value
        pairs, plus the 'nickname' key, and the 'msg_text' key
    :param logger: A Logger object
    """
    logger.debug(f"chat_overlay plugin: {msg}")
