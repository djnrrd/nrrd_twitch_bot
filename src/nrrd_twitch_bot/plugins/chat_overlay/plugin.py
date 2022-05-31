"""An example plugin to provide an OBS chat overlay
"""
from typing import Dict, Union
import os
from html import escape
from aiohttp.web import Request, Response, FileResponse, StreamResponse, \
    WebSocketResponse
from jinja2 import Environment, FileSystemLoader
from nrrd_twitch_bot import BasePlugin, load_config
from .bttv import AsyncBttv


class ChatOverlay(BasePlugin):
    """An OBS Overlay for twitch chat
    """

    def __init__(self, logger):
        super().__init__(logger)
        load_path = os.path.join(os.path.dirname(__file__), 'templates')
        loader = FileSystemLoader(load_path)
        self.jinja_env = Environment(loader=loader)
        self.config = load_config('chat_overlay.ini')
        self.bttv_cache = {}

    async def do_privmsg(self, message: Dict) -> None:
        """Get emotes and pronouns before forwarding the chat message to the
        OBS overlay via the websocket queue

        :param message: Twitch chat privmsg dictionary, with all tags as
            Key/Value pairs, plus the 'nickname' key, and the 'msg_text' key
        """
        message['msg_type'] = 'privmsg'
        message = emote_replacement(message)
        if self.config['DEFAULT'].get('bttv_option', False):
            if not self.bttv_cache:
                await self._update_bttv_cache(message.get('room-id'))
            message = bttv_replacement(message, self.bttv_cache)
        self.logger.debug(f"chat_overlay.plugin.py:  {message}")
        await self.send_web_socket(message)

    async def do_clearchat(self, message: Dict) -> None:
        """Forward clearchat messages to the OBS overlay via the websocket
        queue

        :param message: Twitch chat clearchat dictionary, with all tags as
            Key/Value pairs, plus the 'nickname' key, and the 'msg_text' key
        """
        message['msg_type'] = 'clearchat'
        self.logger.debug(f"chat_overlay.plugin.py: {message}")
        await self.send_web_socket(message)

    async def do_clearmsg(self, message: Dict) -> None:
        """Forward clearmsg messages to the OBS overlay via the websocket
        queue

        :param message: Twitch chat clearmsg dictionary, with all tags as
            Key/Value pairs, plus the 'nickname' key, and the 'msg_text' key
        """
        message['msg_type'] = 'clearmsg'
        self.logger.debug(f"chat_overlay.plugin.py: {message}")
        await self.send_web_socket(message)

    async def http_handler(self, request: Request) \
            -> Union[Response, FileResponse, StreamResponse]:
        """Serve files through the HTTP protocol

        :param request: An aiohttp Request object
        :return: The file to serve through HTTP
        """
        base_path = os.path.join(os.path.dirname(__file__), 'static')
        config = dict(self.config.items('DEFAULT'))
        if request.match_info['path'] == '' \
                or request.match_info['path'] == '/' \
                or request.match_info['path'] == 'index.html':
            self.logger.debug('chat_overlay.plugin.py: sending index page')
            return FileResponse(path=os.path.join(base_path, 'index.html'))
        if request.match_info['path'] == 'overlay.js':
            header = {'Content-type': 'application/ecmascript'}
            self.logger.debug('chat_overlay.plugin.py: sending Javascript')
            jscript_template = self.jinja_env.get_template('overlay.js')
            jscript_file = jscript_template.render(config=config)
            return Response(text=jscript_file, headers=header)
        if request.match_info['path'] == 'style.css':
            header = {'Content-type': 'text/css'}
            self.logger.debug('chat_overlay.plugin.py: sending stylesheet')
            css_template = self.jinja_env.get_template('style.css')
            style_sheet = css_template.render(config=config)
            return Response(text=style_sheet, headers=header)

    async def websocket_handler(self, request: Request) -> WebSocketResponse:
        """Create a websocket instance for the plugin

        :param request: An aiohttp Request object
        :return: The WebSocket response
        """
        return await self._websocket_handler(request)

    async def _update_bttv_cache(self, channel_id: str) -> None:
        """Get the BTTV Emotes for the channel

        :param channel_id: The channel ID as determined from a privmsg tag
        """
        async with AsyncBttv() as bttv:
            self.bttv_cache = await bttv.get_channel_emotes(channel_id)


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


def bttv_replacement(message: Dict, bttv_emotes: Dict) -> Dict:
    """Identify BTTV emotes in a message replacing them with img tags to the
    emotes on BTTV's CDN

    :param message: The message from the Dispatcher
    :param bttv_emotes: The cache of BTTV emotes for the channel.
    :return: The message updated with the IMG tags
    """
    emote_set = [(x['code'], x['id']) for x in bttv_emotes['channelEmotes']]
    emote_set += [(x['code'], x['id']) for x in bttv_emotes['sharedEmotes']]
    # Make sure that we use the longest emote codes first in case the shorter
    # ones clash
    msg_text = message['msg_text']
    for emote in sorted(emote_set, key=lambda x: len(x[0]), reverse=True):
        msg_text = msg_text.replace(emote[0],
                                    f"<img src='https://cdn.betterttv.net/"
                                    f"emote/{emote[1]}/1x' />")
    message['msg_text'] = msg_text
    return message
