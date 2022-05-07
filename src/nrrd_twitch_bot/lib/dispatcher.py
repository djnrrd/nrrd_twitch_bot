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

    :param chat: The TwitchChat object
    :param plugins: The list of plugins to load into the dispatcher
    :param chat_rcv_queue: The Asyncio Queue to receive the messages from the
        TwitchChat object
    :param chat_send_queue: The Asyncio Queue to send messages to the
        TwitchChat object
    :param logger: A logger object
    """
    def __init__(self, chat: TwitchChat, chat_rcv_queue: PriorityQueue,
                 chat_send_queue: PriorityQueue, plugins: List[BasePlugin],
                 logger: Logger) -> None:
        self.chat = chat
        self.chat_rcv_queue = chat_rcv_queue
        self.chat_send_queue = chat_send_queue
        self.logger = logger
        self.plugins = plugins
        self._process_queue: bool = True

    async def shutdown(self) -> None:
        """Shutdown the dispatcher
        """
        self.logger.info('dispatcher.py: Shutting down both Dispatcher queues')
        self._process_queue = False
        # Make sure we're not stuck waiting on the queues
        await self.chat_rcv_queue.put((0, 'SHUTDOWN'))
        await self.chat_send_queue.put((0, 'Shutting down Bot'))

    async def chat_receive(self) -> None:
        """Read messages from the chat queue and dispatch them to plugins
        """
        self.logger.info('dispatcher.py: Starting Dispatcher receive queue')
        while self._process_queue:
            message = await self.chat_rcv_queue.get()
            # It's a priority queue, so get just the message
            message = message[1]
            self.logger.debug(f"dispatcher.py: message: {message}")
            if message == 'PING :tmi.twitch.tv':
                # As well as the keep alive pings and pongs the websockets
                # library manages for us, Twitch sends a specific PING
                # message periodically
                await self.chat.send('PONG :tmi.twitch.tv')
            elif f"PRIVMSG #{self.chat.channel}" in message:
                await self._send_privmsg(message)
            elif f"CLEARCHAT #{self.chat.channel}" in message:
                await self._send_clearchat(message)
            elif f"CLEARMSG #{self.chat.channel}" in message:
                await self._send_clearmsg(message)
            self.chat_rcv_queue.task_done()

    async def chat_send(self) -> None:
        """Send messages back to Twitch chat
        """
        self.logger.info('dispatcher.py: Starting Dispatcher send queue')
        while self._process_queue:
            message = await self.chat_send_queue.get()
            # It's a priority queue, so send just the message
            message = message[1]
            chat_command = f"PRIVMSG #{self.chat.channel} :{message}"
            await self.chat.send(chat_command)
            self.chat_send_queue.task_done()

    async def _send_privmsg(self, message: str) -> None:
        """Send the private messages to all the plugins that implement
        do_privmsg

        :param message: The raw message as received from the websockets queue
        """
        futures = []
        for plugin in self.plugins:
            if hasattr(plugin, 'do_privmsg'):
                futures.append(plugin.do_privmsg(message))
        await asyncio.gather(*futures)

    async def _send_clearchat(self, message: str) -> None:
        """Send the clearchat messages to all the plugins that implement
        do_clearchat

        :param message: The raw message as received from the websockets queue
        """
        futures = []
        for plugin in self.plugins:
            if hasattr(plugin, 'do_clearchat'):
                futures.append(plugin.do_clearchat(message))
        await asyncio.gather(*futures)

    async def _send_clearmsg(self, message: str) -> None:
        """Send the clearmsg messages to all the plugins that implement
        do_clearmsg

        :param message: The raw message as received from the websockets queue
        """
        futures = []
        for plugin in self.plugins:
            if hasattr(plugin, 'do_clearmsg'):
                futures.append(plugin.do_clearmsg(message))
        await asyncio.gather(*futures)

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

    @staticmethod
    def do_privmsg(func: Callable) -> Callable[[str, Logger], Any]:
        """Decorator function for plugins to decorate their do_privmsg functions

        :param func: Plugin do_privmsg function
        :return: The inner wrapper function
        """
        @wraps(func)
        async def inner_wrapper(obj: BasePlugin, msg: str) -> None:
            """Extract the tags and message from the raw privmsg received
            from the websockets client, convert them to a Dictionary and pass
            the dictionary and logger to the decorated functions

            :param obj: The plugin object
            :param msg: The raw message as received from the websockets queue
            """
            tag_dict, irc_user_server, command_text = \
                Dispatcher._split_message(msg, 'PRIVMSG')
            # The Display name is in the tags, so let's take the nickname from
            # the irc_user section
            tag_dict['nickname'] = irc_user_server.split('!')[0]
            tag_dict['msg_text'] = command_text
            obj.logger.debug(f"dispatcher.py: do_privmsg: '{tag_dict}'")
            await func(obj, tag_dict)
        return inner_wrapper

    @staticmethod
    def do_clearchat(func: Callable) -> Callable[[str, Logger], Any]:
        """Decorator function for plugins to decorate their do_clearchat
        functions

        :param func: Plugin do_clearchat function
        :return: The inner wrapper function
        """
        @wraps(func)
        async def inner_wrapper(obj: BasePlugin, msg: str) -> None:
            """Extract the tags and message from the raw clearchat received
            from the websockets client, convert them to a Dictionary and pass
            the dictionary and logger to the decorated functions

            :param obj: The plugin object
            :param msg: The raw message as received from the websockets queue
            """
            tag_dict, irc_user_server, command_text = \
                Dispatcher._split_message(msg, 'CLEARCHAT')
            # If we are clearing user messages the username should be in the
            # command text
            tag_dict['username'] = command_text
            obj.logger.debug(f"dispatcher.py: do_clearchat: '{tag_dict}'")
            await func(obj, tag_dict)
        return inner_wrapper

    @staticmethod
    def do_clearmsg(func: Callable) -> Callable[[str, Logger], Any]:
        """Decorator function for plugins to decorate their do_clearmsg
        functions

        :param func: Plugin do_clearmsg function
        :return: The inner wrapper function
        """
        @wraps(func)
        async def inner_wrapper(obj: BasePlugin, msg: str) -> None:
            """Extract the tags and message from the raw clearmsg received
            from the websockets client, convert them to a Dictionary and pass
            the dictionary and logger to the decorated functions

            :param obj: The plugin object
            :param msg: The raw message as received from the websockets queue
            """
            tag_dict, irc_user_server, command_text = \
                Dispatcher._split_message(msg, 'CLEARMSG')
            # The message to be deleted is in the command_text
            tag_dict['msg_text'] = command_text
            obj.logger.debug(f"dispatcher.py: do_clearmsg: '{tag_dict}'")
            await func(obj, tag_dict)
        return inner_wrapper
