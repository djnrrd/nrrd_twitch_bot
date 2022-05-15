"""Dispatch messages between Twitch chat, plugins and websockets servers
"""
from typing import List, Callable, Any, Dict, Tuple
from logging import Logger
import asyncio
from asyncio import PriorityQueue
from functools import wraps
from .twitch_chat import TwitchChat
from .plugins import BasePlugin


class Dispatcher:
    """Dispatch messages between the Twitch websockets client, plugins
    and the websockets server

    :param plugins: The list of plugins to load into the dispatcher
    :param chat_rcv_queue: The Asyncio Queue to receive the messages from the
        TwitchChat object
    :param chat_send_queue: The Asyncio Queue to send messages to the
        TwitchChat object
    :param logger: A logger object
    """
    def __init__(self, chat_rcv_queue: PriorityQueue,
                 chat_send_queue: PriorityQueue,
                 plugins: List[BasePlugin],
                 logger: Logger) -> None:
        self.chat_rcv_queue = chat_rcv_queue
        self.chat_send_queue = chat_send_queue
        self.logger = logger
        self.plugins = plugins
        self._process_queue: bool = True
        for plugin in self.plugins:
            plugin.dispatcher = self

    async def run(self) -> None:
        """Run the dispatcher queue
        """
        self.logger.info('dispatcher.py: Starting the Dispatcher')
        await self._process_receive_queue()

    async def shutdown(self) -> None:
        """Shutdown the dispatcher
        """
        self.logger.info('dispatcher.py: Shutting down the Dispatcher')
        self._process_queue = False
        # Make sure we're not stuck waiting on the queues
        await self.chat_rcv_queue.put((0, 'SHUTDOWN'))

    async def _process_receive_queue(self) -> None:
        """Read messages from the chat queue and dispatch them to plugins
        """
        self.logger.debug('dispatcher.py: Starting Dispatcher receive queue')
        while self._process_queue:
            message = await self.chat_rcv_queue.get()
            # It's a priority queue, so get just the message
            message = message[1]
            self.logger.debug(f"dispatcher.py: message: {message}")
            if f"PRIVMSG #" in message:
                asyncio.create_task(self._send_privmsg(message))
            elif f"CLEARCHAT #" in message:
                asyncio.create_task(self._send_clearchat(message))
            elif f"CLEARMSG #" in message:
                asyncio.create_task(self._send_clearmsg(message))
            self.chat_rcv_queue.task_done()

    async def chat_send(self, message: str) -> None:
        """Send messages back through the chat queue for the twitch chat
        service

        :param message: The message to send back to chat.
        """
        asyncio.create_task(self.chat_send_queue.put((0, message)))

    @staticmethod
    def _split_message(message: str, command: str) -> Tuple[Dict, str, str]:
        """Split the tags out from the received websockets frame

        :param message: The websockets frame
        :param command:
        :return:
        """
        tag_dict = {}
        # Find the command
        msg_start = message.find(command)
        # Everything previous to the command should be tags and the IRC user
        # and server section. Let's do a colon split then rejoin knowing the
        # IRC user and server section is on the end
        parts = message[:msg_start].split(':')
        tags = ':'.join(parts[:-1])
        irc_user_server = parts[-1]
        # Tags will be preceded by an @ symbol. We don't need that. Each
        # tag is semicolon separated
        # https://dev.twitch.tv/docs/irc/tags#privmsg-twitch-tags
        tags = tags[1:].split(';')
        for tag in tags:
            # Tags are in a key=value format, but may not have values
            tag_parts = tag.split('=')
            tag_dict[tag_parts[0]] = tag_parts[1]
        # Finally, the command text which we'll do the colon split and
        # rejoin on and strip the carriage returns
        command_text = ':'.join(message[msg_start:].split(':')[1:]).strip()
        return tag_dict, irc_user_server, command_text

    async def _send_privmsg(self, message: str) -> None:
        """Send the private messages to all the plugins that implement
        do_privmsg

        :param message: The raw message as received from the websockets queue
        """
        tag_dict, irc_user_server, command_text = \
            self._split_message(message, 'PRIVMSG')
        # The Display name is in the tags, so let's take the nickname from
        # the irc_user section
        tag_dict['nickname'] = irc_user_server.split('!')[0]
        tag_dict['msg_text'] = command_text
        self.logger.debug(f"dispatcher.py: _send_privmsg: tag_dict {tag_dict}")
        futures = []
        for plugin in self.plugins:
            if hasattr(plugin, 'do_privmsg'):
                futures.append(plugin.do_privmsg(tag_dict))
        await asyncio.gather(*futures)

    async def _send_clearchat(self, message: str) -> None:
        """Send the clearchat messages to all the plugins that implement
        do_clearchat

        :param message: The raw message as received from the websockets queue
        """
        tag_dict, irc_user_server, command_text = \
            self._split_message(message, 'CLEARCHAT')
        # If we are clearing user messages the username should be in the
        # command text
        tag_dict['username'] = command_text
        self.logger.debug(f"dispatcher.py: _send_clearchat: tag_dict"
                          f" {tag_dict}")
        futures = []
        for plugin in self.plugins:
            if hasattr(plugin, 'do_clearchat'):
                futures.append(plugin.do_clearchat(tag_dict))
        await asyncio.gather(*futures)

    async def _send_clearmsg(self, message: str) -> None:
        """Send the clearmsg messages to all the plugins that implement
        do_clearmsg

        :param message: The raw message as received from the websockets queue
        """
        tag_dict, irc_user_server, command_text = \
            self._split_message(message, 'CLEARMSG')
        # The message to be deleted is in the command_text
        tag_dict['msg_text'] = command_text
        self.logger.debug(f"dispatcher.py: _send_clearmsg: tag_dict {tag_dict}")
        futures = []
        for plugin in self.plugins:
            if hasattr(plugin, 'do_clearmsg'):
                futures.append(plugin.do_clearmsg(tag_dict))
        await asyncio.gather(*futures)
