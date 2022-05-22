"""An example plugin to provide a basic chat commands bot
"""
from typing import Dict
import asyncio
from nrrd_twitch_bot import BasePlugin


class ChatCommands(BasePlugin):
    """A basic chat command bot
    """

    async def do_privmsg(self, message: Dict) -> None:
        """Log the message dictionary from the dispatcher to the logger object

        :param message: Websockets privmsg dictionary, with all tags as
            Key/Value pairs, plus the 'nickname' key, and the 'msg_text' key
        """
        if message['msg_text'][0] != '!':
            return
        command = message['msg_text'].split(' ')[0][1:]
        self.logger.debug(f"chat_commands: command {command} received")
        response = self.chat_commands(command)
        if response:
            self.logger.debug(f"chat_command: response is {response}")
            asyncio.create_task(self.dispatcher.chat_send(response))

    @staticmethod
    def chat_commands(command: str):
        """Return the response to the chat commands

        :param command: the extracted command
        :return: the command response
        """
        commands = {'oar': 'Hit it with an oar!',
                    'catbutt': 'djnrrdCats DJ Has cats and a web camera. '
                               'djnrrdSnarf you know where this is going to '
                               'end up djnrrdOrko'}
        return commands.get(command)
