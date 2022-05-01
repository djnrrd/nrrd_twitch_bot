""""Module for connecting to the Twitch Websockets chat service
"""
from typing import Optional, Type, Union
from types import TracebackType
from asyncio import PriorityQueue
from logging import Logger
from websockets import client


class TwitchChat:
    """Connect to the twitch chat service.

    This should be used with the Asynchronous context manager and the run()
    method invoked.

    async with TwitchChat(token, nick, channel, logger) as twitch:
        await twitch.run()

    :param oauth_token: OAuth2 token received from Twitch
    :param nickname: Twitch username
    :param channel: Twitch channel to join
    :param logger: A logger object
    """

    def __init__(self, oauth_token: str, nickname: str, channel: str,
                 logger: Logger, dispatch_queue: PriorityQueue) -> None:
        self.uri: str = 'wss://irc-ws.chat.twitch.tv:443'
        self.oauth_token = oauth_token
        self.nickname = nickname
        self.channel = channel.lower()
        self.logger = logger
        self._session: Union[client.WebSocketClientProtocol, None] = None
        self.dispatch_queue = dispatch_queue

    def __enter__(self) -> None:
        """Should not be using with the normal context manager"""
        raise TypeError("Use async with instead")

    def __exit__(self,
                 exc_type: Optional[Type[BaseException]],
                 exc_val: Optional[BaseException],
                 exc_tb: Optional[TracebackType]) -> None:
        """This should never be called but is required for the normal context
        manager"""
        pass

    async def __aenter__(self) -> 'TwitchChat':
        """Entry point for the async context manager"""
        await self.open()
        return self

    async def __aexit__(self,
                        exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]) -> None:
        """Exit point for the async context manager"""
        await self.close()

    async def open(self) -> None:
        """Open a websockets client that's stored in the object"""
        self.logger.info('twitch_chat.py: Starting TwitchChat client')
        if not self._session:
            self.logger.debug('twitch_chat.py: Starting session')
            self._session = await client.connect(self.uri, logger=self.logger)
            if not await self._login():
                await self.close()

    async def close(self) -> None:
        """Close the  websockets client stored in the object"""
        self.logger.info('twitch_chat.py: Shutting down TwitchChat client')
        if self._session:
            try:
                self.logger.debug('twitch_chat.py: Attempting to close session')
                await self._session.close()
            except BaseException as exception:
                raise exception
            finally:
                self._session = None

    async def _login(self) -> Union[bool, None]:
        """Log into the twitch chat service, request the appropriate features
        and join the requested channel

        :return: True if everything went OK.
        """
        if not await self._authentication():
            return None
        if not await self._request_features():
            return None
        if not await self._join_channel():
            return None
        return True

    async def _authentication(self) -> Union[bool, None]:
        """Authenticate to the twitch chat service

        :return: True if authenticated.
        """
        await self.send(f"PASS oauth:{self.oauth_token}")
        await self.send(f"NICK {self.nickname}")
        result = await self._session.recv()
        self.logger.debug(f"twitch_chat.py: Login: {result}")
        if 'Login authentication failed' in result:
            self.logger.error(f"twitch_chat.py: Login authentication failed: "
                              f"{result}")
            self.logger.error('twitch_chat.py: Please check Twitch settings '
                              'and re-authorise application')
            return None
        return True

    async def _request_features(self) -> Union[bool, None]:
        """Request the IRC features of Twitch Chat

        :return: True if all features were acknowledged
        """
        await self.send('CAP REQ :twitch.tv/membership')
        result = await self._session.recv()
        self.logger.debug(f"twitch_chat.py: Req Membership: {result}")
        if 'ACK :twitch.tv/membership' not in result:
            return None
        await self.send('CAP REQ :twitch.tv/tags')
        result = await self._session.recv()
        self.logger.debug(f"twitch_chat.py: Req Tags: {result}")
        if 'ACK :twitch.tv/tags' not in result:
            return None
        await self.send('CAP REQ :twitch.tv/commands')
        result = await self._session.recv()
        self.logger.debug(f"twitch_chat.py: Req commands: {result}")
        if 'ACK :twitch.tv/commands' not in result:
            return None
        return True

    async def _join_channel(self) -> Union[bool, None]:
        """Join the requested channel

        :return: True if the JOIN was successful
        """
        await self.send(f"JOIN #{self.channel}")
        result = await self._session.recv()
        self.logger.debug(f"twitch_chat.py: Join: {result}")
        if f"JOIN #{self.channel}" not in result:
            return None
        return True

    async def send(self, message: str) -> None:
        """Send a message to the Twitch websockets server

        :param message: The message to send
        """
        await self._session.send(message)

    async def run(self) -> None:
        """Run the chat session
        """
        if self._session:
            async for frame in self._session:
                # Messages may be multiline, split with '\r\n' and always have
                # '\r\n' at the end of the message
                frame = frame.strip()
                messages = frame.split('\r\n')
                for message in messages:
                    self.logger.debug(f"twitch_chat.py: Run: {message}")
                    await self.dispatch_queue.put((0, message))
