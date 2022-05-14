"""An example plugin to provide an OBS chat overlay
"""
from typing import Dict, Union, List
from logging import Logger
from datetime import datetime, timedelta
import asyncio
import os
from html import escape
import aiohttp
from aiohttp.web import Request, Response, FileResponse, StreamResponse, \
    WebSocketResponse
from nrrd_twitch_bot import Dispatcher, BasePlugin


class ChatOverlay(BasePlugin):
    """An OBS Overlay for twitch chat
    """

    def __init__(self, logger: Logger):
        super().__init__(logger)
        self.user_cache = {}
        self.pronouns = load_pronouns(self.logger)

    async def do_privmsg(self, message: Dict, dispatcher: Dispatcher) -> None:
        """Get emotes and pronouns before forwarding the chat message to the
        OBS overlay via the websocket queue

        :param message: Twitch chat privmsg dictionary, with all tags as
            Key/Value pairs, plus the 'nickname' key, and the 'msg_text' key
        :param dispatcher: The dispatcher object to send messages back to chat
        """
        message['msg_type'] = 'privmsg'
        message = emote_replacement(message)
        message = await self.get_pronouns(message)
        self.logger.debug(f"chat_overlay.plugin.py:  {message}")
        await self.websocket_queue.put(message)

    async def do_clearchat(self, message: Dict, dispatcher: Dispatcher) -> None:
        """Forward clearchat messages to the OBS overlay via the websocket
        queue

        :param message: Twitch chat clearchat dictionary, with all tags as
            Key/Value pairs, plus the 'nickname' key, and the 'msg_text' key
        :param dispatcher: The dispatcher object to send messages back to chat
        """
        message['msg_type'] = 'clearchat'
        self.logger.debug(f"chat_overlay.plugin.py: {message}")
        await self.websocket_queue.put(message)

    async def do_clearmsg(self, message: Dict, dispatcher: Dispatcher) -> None:
        """Forward clearmsg messages to the OBS overlay via the websocket
        queue

        :param message: Twitch chat clearmsg dictionary, with all tags as
            Key/Value pairs, plus the 'nickname' key, and the 'msg_text' key
        :param dispatcher: The dispatcher object to send messages back to chat
        """
        message['msg_type'] = 'clearmsg'
        self.logger.debug(f"chat_overlay.plugin.py: {message}")
        await self.websocket_queue.put(message)

    async def http_handler(self, request: Request) \
            -> Union[Response, FileResponse, StreamResponse]:
        """Serve files through the HTTP protocol

        :param request: An aiohttp Request object
        :return: The file to serve through HTTP
        """
        base_path = os.path.join(os.path.dirname(__file__), 'static')
        if request.match_info['path'] == '' \
                or request.match_info['path'] == '/' \
                or request.match_info['path'] == 'index.html':
            self.logger.debug('chat_overlay.plugin.py: sending index page')
            return FileResponse(path=os.path.join(base_path, 'index.html'))
        if request.match_info['path'] == 'overlay.js':
            header = {'Content-type': 'application/ecmascript'}
            self.logger.debug('chat_overlay.plugin.py: sending Javascript')
            return FileResponse(path=os.path.join(base_path, 'overlay.js'),
                                headers=header)
        if request.match_info['path'] == 'style.css':
            header = {'Content-type': 'text/css'}
            self.logger.debug('chat_overlay.plugin.py: sending stylesheet')
            return FileResponse(path=os.path.join(base_path, 'style.css'),
                                headers=header)

    async def websocket_handler(self, request: Request) -> WebSocketResponse:
        """Create a websocket instance for the plugin

        :param request: An aiohttp Request object
        :return: The WebSocket response
        """
        return await self._websocket_handler(request)

    async def get_pronouns(self, message: Dict) -> Dict:
        """Get a user's pronouns from the alejo.io service

        :param message:
        :return:
        """
        nickname = message['nickname']
        self.logger.debug(f"chat_overlay.plugin.py: looking up pronouns for "
                          f"user {nickname}")
        if self.user_cache.get(nickname):
            five_minutes = timedelta(minutes=5)
            time_diff = datetime.now() - self.user_cache[nickname][1]
            if time_diff > five_minutes:
                self.logger.debug(f"chat_overlay.plugin.py: cache expired for "
                                  f"{nickname}, refreshing")
                await self.lookup_pronouns(nickname)
                return await self.get_pronouns(message)
            else:
                pronouns = self.user_cache[nickname][0]
                self.logger.debug(f"chat_overlay.plugin.py: {nickname} found "
                                  f"with pronouns {pronouns}")
        else:
            self.logger.debug(f"chat_overlay.plugin.py: user {nickname} not "
                              f"found in cache")
            await self.lookup_pronouns(nickname)
            return await self.get_pronouns(message)
        message['pronouns'] = pronouns
        return message

    async def lookup_pronouns(self, nickname: str) -> None:
        """Lookup a user's pronouns on the alejo.io service and add them to
        the cache

        :param nickname: The user's nickname in chat (not the display name)
        """
        self.logger.debug(f"chat_overlay.plugin.py: Loading pronouns for user "
                          f"{nickname}")
        user_pronouns = await async_load_pronouns(f"users/{nickname}",
                                                  self.logger)
        if user_pronouns:
            # A list is returned, although only one pronoun set is linked to
            # the user
            pronoun_id = user_pronouns[0]['pronoun_id']
            self.user_cache[nickname] = (self.pronouns[pronoun_id], datetime.now())
        else:
            self.user_cache[nickname] = (None, datetime.now())


def emote_replacement(message: Dict) -> Dict:
    """Escape HTML characters in the text and identify emotes in a message
    replacing them with img tags to the emotes on Twitch's CDN

    :param message: The message from the Dispatcher
    :return: The message updated with escaped HTML and the IMG tags
    """
    # Identify emotes and placements, multiple emotes are split by '/',
    # emote uuid and placements is separated by ':'. Multiple placements
    # are split by ',' and the start and end placements are split by '-'
    if message.get('emotes'):
        emote_list = []
        for emote in message.get('emotes').split('/'):
            emote_uuid = emote.split(':')[0]
            placements = emote.split(':')[1]
            for placement in placements.split(','):
                start_mark = placement.split('-')[0]
                end_mark = placement.split('-')[1]
                start_mark = int(start_mark)
                # Add 1 to the end marker to make python slices work
                end_mark = int(end_mark) + 1
                emote_list.append((start_mark, end_mark, emote_uuid))
        # Start working through the message, escaping HTML inbetween the
        # emotes
        end_section = 0
        msg_parts = []
        for emote in sorted(emote_list, key=lambda x: x[0]):
            pre_text = escape(message['msg_text'][end_section:emote[0]],
                              quote=True)
            emote_html = f"<img src='https://static-cdn.jtvnw.net/" \
                         f"emoticons/v2/{emote[2]}/default/light/1.0' />"
            msg_parts += [pre_text, emote_html]
            end_section = emote[1]
        post_text = escape(message['msg_text'][end_section:], quote=True)
        msg_parts.append(post_text)
        message['msg_text'] = ''.join(msg_parts)
    else:
        # Escape HTML characters in the whole message instead
        message['msg_text'] = escape(message['msg_text'], quote=True)
    return message


def load_pronouns(logger: Logger) -> Dict:
    """Load the sets of pronouns from the alejo.io service

    :return:
    """
    pronouns = asyncio.run(async_load_pronouns('pronouns', logger))
    if pronouns:
        logger.debug(f"chat_overlay.plugin.py: got {len(pronouns)} back from "
                     f"alejo.io pronoun list")
        pronouns = {x['name']: x['display'] for x in pronouns}
    return pronouns


async def async_load_pronouns(path: str, logger: Logger) -> List:
    """Load the sets of pronouns from the alejo.io service

    :return:
    """
    headers = {'Accept': 'application/json'}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f"https://pronouns.alejo.io/api/{path}") \
                as resp:
            logger.debug(f"chat_overlay.plugin.py: got status {resp.status} "
                         f"from alejo.io pronoun service")
            if resp.status == 200:
                pronoun_response = await resp.json()
                logger.debug(f"chat_overlay.plugin.py: got {pronoun_response} "
                             f"from alejo.io service")
            else:
                pronoun_response = None
    return pronoun_response
