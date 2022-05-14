"""An example plugin to provide an OBS chat overlay
"""
from typing import Dict, Union
import os
from html import escape
from aiohttp.web import Request, Response, FileResponse, StreamResponse, \
    WebSocketResponse
from nrrd_twitch_bot import Dispatcher, BasePlugin


class ChatOverlay(BasePlugin):
    """An OBS Overlay for twitch chat
    """

    async def do_privmsg(self, message: Dict, dispatcher: Dispatcher) -> None:
        """Add emotes to the

        :param message: Websockets privmsg dictionary, with all tags as Key/Value
            pairs, plus the 'nickname' key, and the 'msg_text' key
        """
        message['msg_type'] = 'privmsg'
        message = emote_replacement(message)
        self.logger.debug(f"chat_overlay.plugin.py:  {message}")
        await self.websocket_queue.put(message)

    async def do_clearchat(self, message: Dict, dispatcher: Dispatcher) -> None:
        message['msg_type'] = 'clearchat'
        self.logger.debug(f"chat_overlay.plugin.py: {message}")
        await self.websocket_queue.put(message)

    async def do_clearmsg(self, message: Dict, dispatcher: Dispatcher) -> None:
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
