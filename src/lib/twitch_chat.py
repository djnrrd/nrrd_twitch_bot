""""Module for connecting to the Twitch Websockets chat service
"""
from typing import Optional, Type, Union
from types import TracebackType
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
                 logger: Logger) -> None:
        self.uri: str = 'wss://irc-ws.chat.twitch.tv:443'
        self.oauth_token = oauth_token
        self.nickname = nickname
        self.channel = channel.lower()
        self.logger = logger
        self._session: Union[client.WebSocketClientProtocol, None] = None

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
        self.logger.debug('TwitchChat Open called')
        if not self._session:
            self.logger.debug('Starting session')
            self._session = await client.connect(self.uri, logger=self.logger)
            if not await self.authentication():
                await self.close()

    async def close(self) -> None:
        """Close the  websockets client stored in the object"""
        self.logger.debug('TwitchChat Close called')
        if self._session:
            try:
                self.logger.debug('Attempting to close session')
                await self._session.close()
            except BaseException as exception:
                raise exception
            finally:
                self._session = None

    async def authentication(self) -> Union[bool, None]:
        """Authenticate to the twitch chat service
        """
        if self._session:
            try:
                await self.send(f"PASS oauth:{self.oauth_token}")
                await self.send(f"NICK {self.nickname}")
                result = await self._session.recv()
                if 'Login authentication failed' in result:
                    self.logger.error('Login authentication failed. Please '
                                      'check Twitch settings and re-authorise '
                                      'application')
                    return None
                await self.send(f"JOIN #{self.channel}")
                await self.send('CAP REQ :twitch.tv/membership')
                await self.send('CAP REQ :twitch.tv/tags')
                await self.send('CAP REQ :twitch.tv/commands')
                return True
            except BaseException as exception:
                raise exception

    async def send(self, message: str) -> None:
        """Send a message to the Twitch websockets server

        :param message: The message to send
        """
        await self._session.send(message)

    async def run(self) -> None:
        """Run the chat session
        """
        if self._session:
            async for message in self._session:
                # As well as the keep alive pings and pongs the websockets
                # library manages for us, Twitch send a specific PING message
                # periodically
                if message.strip() == 'PING :tmi.twitch.tv':
                    await self._session.send('PONG :tmi.twitch.tv')
                elif f"PRIVMSG #{self.channel}" in message:
                    await self._privmsg_rcv(message)

    async def _privmsg_rcv(self, message: str) -> None:
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
        self.logger.info(f"Message : '{privmsg}'")
