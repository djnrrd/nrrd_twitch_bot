from typing import Dict
from logging import Logger
from lib.dispatcher import BotDispatcher
from asyncio import PriorityQueue


@BotDispatcher.do_privmsg
async def do_privmsg(msg: Dict, send_queue: PriorityQueue, logger: Logger) \
        -> None:
    """Look for chat commands and return the responses

    :param msg: Websockets privmsg dictionary, with all tags as Key/Value
        pairs, plus the 'nickname' key, and the 'msg_text' key
    :param send_queue: The queue object to send messages back to TwitchChat
    :param logger: A Logger object
    """
    if msg['msg_text'][0] != '!':
        return
    command = msg['msg_text'].split(' ')[0][1:]
    logger.debug(f"chat_commands: command {command} received")
    response = chat_commands(command)
    if response:
        logger.debug(f"chat_command: response is {response}")
        await send_queue.put((0, response))


def chat_commands(command: str):
    commands = {'oar': 'Hit him with an oar!',
                'catbutt': 'DJ Has cas and a web camera. How did you think '
                           'this would end?'}
    return commands.get(command)
