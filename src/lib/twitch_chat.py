""""Module for connecting to the Twitch Websockets chat service
"""
from typing import Optional, Type
from types import TracebackType
from websockets import client
from logging import Logger
from datetime import datetime, timedelta


class TwitchChat:
    """Connect to the twitch chat service.

    This should be used with the Asynchronous context manager and the run()
    method invoked.

    async with TwitchChat(token, nick, channel, logger) as twitch:
        twitch.run()

    :param oauth_token: OAuth2 token received from Twitch
    :param nickname: Twitch username
    :param channel: Twitch channel to join
    :param logger: A logger object
    """

    def __init__(self, oauth_token: str, nickname: str, channel: str,
                 logger: Logger) -> None:
        self.uri: str = 'wss://irc-ws.chat.twitch.tv:443'
        self.oauth_token = oauth_token
        self.nickname = nickname
        self.channel = channel
        self.logger = logger
        self._session: client.WebSocketClientProtocol = None

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

    async def open(self) -> 'TwitchChat':
        """Open a websockets client that's stored in the object"""
        if not self._session:
            self._session = await client.connect(self.uri, logger=self.logger)
            await self.authentication()
        return self

    async def close(self) -> None:
        """Close the  websockets client stored in the object"""
        if self._session:
            try:
                await self._session.close()
            except BaseException as exception:
                raise exception
            finally:
                self._session = None

    async def authentication(self) -> None:
        """Authenticate to the twitch chat service
        """
        if self._session:
            try:
                await self._session.send(f"PASS oauth:{self.oauth_token}")
                await self._session.send(f"NICK {self.nickname}")
                await self._session.send(f"JOIN #{self.channel.lower()}")
                await self._session.send('CAP REQ :twitch.tv/membership')
                await self._session.send('CAP REQ :twitch.tv/tags')
                await self._session.send('CAP REQ :twitch.tv/commands')
            except BaseException as exception:
                raise exception

    async def run(self) -> None:
        """Run the chat session
        """
        start_time = datetime.now()
        async for message in self._session:
            # As well as the keep alive pings and pongs the websockets
            # library manages for us, Twitch send a specific PING message
            # periodically
            if message.strip() == 'PING :tmi.twitch.tv':
                await self._session.send('PONG :tmi.twitch.tv')
            else:
                await self._message_rcv(message)
            message_time = datetime.now()
            if message_time - start_time >= timedelta(minutes=2):
                self.logger.info('Exiting run loop after time expired')
                break

    async def _message_rcv(self, message: str) -> None:
        """Do something with the messages from the server

        :param message:
        :return:
        """
        self.logger.info(f"Message received: '{message}'")
