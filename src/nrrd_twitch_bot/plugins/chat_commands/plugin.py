"""An example plugin to provide a basic chat commands bot
"""
from typing import Dict
import asyncio
from nrrd_twitch_bot import Dispatcher, BasePlugin


class ChatCommands(BasePlugin):
    """An OBS Overlay for twitch chat
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def do_privmsg(self, message: Dict, dispatcher: Dispatcher) -> None:
        """Log the message dictionary from the dispatcher to the logger object

        :param message: Websockets privmsg dictionary, with all tags as
            Key/Value pairs, plus the 'nickname' key, and the 'msg_text' key
        :param dispatcher: The dispatcher object for sending messages back to
            Twitch chat
        """
        if message['msg_text'][0] != '!':
            return
        command = message['msg_text'].split(' ')[0][1:]
        self.logger.debug(f"chat_commands: command {command} received")
        response = self.chat_commands(command)
        if response:
            self.logger.debug(f"chat_command: response is {response}")
            asyncio.create_task(dispatcher.chat_send(response))

    def chat_commands(self, command: str):
        """Return the response to the chat commands

        :param command: the extracted command
        :return: the command response
        """
        commands = {'oar': 'Hit him with an oar!',
                    'catbutt': 'DJ Has cas and a web camera. How did you think '
                               'this would end?'}
        return commands.get(command)

