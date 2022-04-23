"""Dispatch messages between Twitch chat, plugins and websockets servers
"""
import asyncio
from typing import List, Callable, Any
from logging import Logger
from asyncio import PriorityQueue
from functools import wraps
from .twitch_chat import TwitchChat
from .plugins import load_dispatchers

class BotDispatcher:
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
                 chat_send_queue: PriorityQueue, logger: Logger) -> None:
        self.chat = chat
        self.chat_rcv_queue = chat_rcv_queue
        self.chat_send_queue = chat_send_queue
        self.logger = logger
        self.plugins = load_dispatchers(self.logger)
        self._process_queue: bool = True

    async def shutdown(self) -> None:
        """Shutdown the dispatcher
        """
        self.logger.debug('Dispatcher received shutdown')
        self._process_queue = False
        # Make sure we're not stuck waiting on the queues
        await self.chat_rcv_queue.put((0, 'SHUTDOWN'))
        await self.chat_send_queue.put((0, 'Shutting down Bot'))

    async def chat_receive(self) -> None:
        """Read messages from the chat queue and dispatch them to plugins
        """
        while self._process_queue:
            message = await self.chat_rcv_queue.get()
            # It's a priority queue, so get just the message
            message = message[1]
            self.logger.debug(f"Dispatcher: {message}")
            if message == 'PING :tmi.twitch.tv':
                # As well as the keep alive pings and pongs the websockets
                # library manages for us, Twitch sends a specific PING
                # message periodically
                await self.chat.send('PONG :tmi.twitch.tv')
            elif f"PRIVMSG #{self.chat.channel}" in message:
                await self._send_privmsg(message)
            self.chat_rcv_queue.task_done()

    async def chat_send(self) -> None:
        """Send messages back to Twitch chat
        """
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
                futures.append(plugin.do_privmsg(message,
                                                 self.chat_send_queue,
                                                 self.logger))
        await asyncio.gather(*futures)

    @staticmethod
    def do_privmsg(func: Callable) -> Callable[[str, Logger], Any]:
        """Decorator function for plugins to decorate their do_privmsg functions

        :param func: Plugin do_privmsg function
        :return: The inner wrapper function
        """
        @wraps(func)
        async def inner_wrapper(msg: str, chat_send_queue: PriorityQueue,
                                logger: Logger) -> None:
            """Extract the tags and message from the raw privmsg received
            from the websockets client, convert them to a Dictionary and pass
            the dictionary and logger to the decorated functions

            :param msg: The raw message as received from the websockets queue
            :param chat_send_queue: The queue object to send messages back to
                TwitchChat
            :param logger: a logger object
            """
            privmsg = {}
            # Break the message into its parts, which should be colon separated.
            parts = msg.split(':')
            # The tags should be in the first colon separated section,
            # they'll be preceded by an @ symbol. We don't need that. Each
            # tag is semicolon separated
            # https://dev.twitch.tv/docs/irc/tags#privmsg-twitch-tags
            tags = parts[0][1:].split(';')
            for tag in tags:
                # Tags are in a key=value format, but may not have values
                tag_parts = tag.split('=')
                privmsg[tag_parts[0]] = tag_parts[1]
            # The Display name is in the tags, so let's take the nickname from
            # the prefix.
            privmsg['nickname'] = parts[1].split('!')[0]
            # Finally, the message, which may have had colons in it, so let's
            # rejoin
            privmsg['msg_text'] = ':'.join(parts[2:]).strip()
            logger.debug(f"do_privmsg: '{privmsg}'")
            await func(privmsg, chat_send_queue, logger)
        return inner_wrapper
