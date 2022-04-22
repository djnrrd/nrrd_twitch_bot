"""Dispatch messages between Twitch chat, plugins and websockets servers
"""
from asyncio import Queue
from .twitch_chat import TwitchChat
from logging import Logger


class BotDispatcher:

    def __init__(self, chat: TwitchChat, chat_queue: Queue, logger: Logger) \
            -> None:
        """

        :param chat:
        :param chat_queue:
        :param logger:
        """
        self.chat = chat
        self.chat_queue = chat_queue
        self.logger = logger
        self._process_queue: bool = True

    async def shutdown(self) -> None:
        """Shutdown the dispatcher
        """
        self.logger.debug('Dispatcher received shutdown')
        self._process_queue = False
        # Make sure we're not stuck waiting on the queue
        await self.chat_queue.put((0, 'SHUTDOWN'))

    async def run(self) -> None:
        """Read messages from the chat queue and dispatch them to plugins
        """
        while self._process_queue:
            message = await self.chat_queue.get()
            message = message[1]
            self.logger.debug(f"Dispatcher: {message}")
            if message == 'PING :tmi.twitch.tv':
                # As well as the keep alive pings and pongs the
                # websockets library manages for us, Twitch sends a
                # specific PING message periodically
                await self.chat.send('PONG :tmi.twitch.tv')
            elif f"PRIVMSG #{self.chat.channel}" in message:
                await self.on_privmsg(message)
            self.chat_queue.task_done()

    async def on_privmsg(self, message: str) -> None:
        """Do something with the channel messages from the server

        :param message: The message sent to the channel
        """
        privmsg = {}
        # Break the message into its parts, which should be colon separated.
        parts = message.split(':')
        # The tags should be in the first colon separated section, they'll be
        # preceded by an @ symbol. We don't need that. Each tag is semi-colon
        # separated
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
        self.logger.info(f"on_privmsg : '{privmsg}'")
