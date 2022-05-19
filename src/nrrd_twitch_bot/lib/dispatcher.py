"""Dispatch messages between Twitch chat, plugins and websockets servers
"""
from typing import List, Callable, Any, Dict, Tuple
from logging import Logger
import asyncio
from asyncio import PriorityQueue
import re
from .plugins import BasePlugin
from .twitch_helix import get_emote_sets


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
        self.user: str = ''
        self.user_state: Dict = {}
        self.user_emotes: Dict = {}
        self.room: str = ''
        self.room_state: Dict = {}
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
            if 'PRIVMSG #' in message:
                asyncio.create_task(self._send_privmsg(message))
            elif 'CLEARCHAT #' in message:
                asyncio.create_task(self._send_clearchat(message))
            elif 'CLEARMSG #' in message:
                asyncio.create_task(self._send_clearmsg(message))
            elif 'ROOMSTATE #' in message:
                asyncio.create_task(self._send_roomstate(message))
            elif 'USERSTATE #' in message:
                asyncio.create_task(self._send_userstate(message))
            elif 'tmi.twitch.tv 353' in message:
                self._update_user_room(message)
            self.chat_rcv_queue.task_done()

    def _update_user_room(self, message: str) -> None:
        """Use the RPL_NAMREPLY reply to joining the IRC room to determine
        the user and room name.  This message may happen twice if there are
        existing users, however the second one will have the correct user
        details, so we might as well let it run twitch

        :param message: the RPL_NAMREPLY reply message
        """
        parts = message.split(':')
        self.user = parts[-1]
        self.room = parts[-2].split()[-1]

    async def chat_send(self, message: str) -> None:
        """Send messages back through the chat queue for the twitch chat
        service. This does not get echoed back from Twitch so a mock message
        needs to be created and sent back into the Queue

        :param message: The message to send back to chat.
        """
        asyncio.create_task(self.chat_send_queue.put((0, message)))
        tags = [f"{x}={y}" for x, y in self.user_state.items()]
        emotes = []
        for emote, emote_id in self.user_emotes.items():
            matches = [m.start() for m in re.finditer(re.escape(emote),
                                                      message)]
            if matches:
                markers = ','.join([f"{x}-{len(emote) - 1 + x}" for x in
                                    matches])
                emotes.append(f"{emote_id}:{markers}")
        emotes = '/'.join(emotes)
        tags.append(f"emotes={emotes}")
        fake_message = f"@{';'.join(tags)}:{self.user}!{self.user}@" \
                       f"{self.user}.tmi.twitch.tv PRIVMSG #{self.room} :" \
                       f"{message}"
        await self.chat_rcv_queue.put((0, fake_message))

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

    async def _send_roomstate(self, message: str) -> None:
        """Send the roomstate messages to all the plugins that implement
        do_roomstate, and update the Dispatcher with the roomstate info

        :param message: The raw message as received from the websockets queue
        """
        tag_dict, irc_user_server, command_text = \
            self._split_message(message, 'ROOMSTATE')
        self.room_state = tag_dict
        self.logger.debug(f"dispatcher.py: _send_roomstate: tag_dict"
                          f" {tag_dict}")
        futures = []
        for plugin in self.plugins:
            if hasattr(plugin, 'do_roomstate'):
                futures.append(plugin.do_roomstate(tag_dict))
        await asyncio.gather(*futures)

    async def _send_userstate(self, message: str) -> None:
        """Send the userstate messages to all the plugins that implement
        do_userstate, and update the Dispatcher with the userstate info

        :param message: The raw message as received from the websockets queue
        """
        tag_dict, irc_user_server, command_text = \
            self._split_message(message, 'USERSTATE')
        self.user_state = tag_dict
        self.logger.debug(f"dispatcher.py: _send_userstate: tag_dict"
                          f" {tag_dict}")
        asyncio.create_task(self._update_user_emotes(tag_dict))
        futures = []
        for plugin in self.plugins:
            if hasattr(plugin, 'do_userstate'):
                futures.append(plugin.do_userstate(tag_dict))
        await asyncio.gather(*futures)

    async def _update_user_emotes(self, user_state: Dict) -> None:
        """Update the user's locally stored available emotes

        :param user_state:
        :return:
        """
        emote_set_ids = user_state['emote-sets'].split(',')
        emote_sets = await get_emote_sets(emote_set_ids, self.logger)
        emote_dict = {}
        for emote_set in emote_sets:
            tmp_dict = {x['name']: x['id'] for x in emote_set}
            emote_dict.update(tmp_dict)
        self.user_emotes.update(emote_dict)
