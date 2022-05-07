"""An example plugin to provide an OBS chat overlay
"""
from typing import Dict, Union
import os
import json
from aiohttp.web import Request, Response, FileResponse, StreamResponse, \
    WebSocketResponse
from nrrd_twitch_bot import Dispatcher, BasePlugin


class ChatOverlay(BasePlugin):
    """An OBS Overlay for twitch chat
    """

    @Dispatcher.do_privmsg
    async def do_privmsg(self, message: Dict) -> None:
        """Log the message dictionary from the dispatcher to the logger object

        :param message: Websockets privmsg dictionary, with all tags as Key/Value
            pairs, plus the 'nickname' key, and the 'msg_text' key
        """
        # Replace emote text with emote images
        if message.get('emotes'):
            # multiple emotes are / separated but don't replace them straight
            # away
            emotes = message['emotes'].split('/')
            emote_list = []
            for emote in emotes:
                # The CDN UUID of the emote and the emote location are :
                # separated
                emote_code = emote.split(':')[0]
                emote_url = f"<img src='https://static-cdn.jtvnw.net/" \
                            f"emoticons/v2/{emote_code}/default/light/1.0' />"
                # An emote may be repeated multiple times, positions are ,
                # separated. But we only need the first one to work out the
                # emote text
                emote_markers = emote.split(':')[1].split(',')[0]
                # Finally, the start and the end markers are - separated but
                # for python slicing we need to add 1 to the end marker
                emote_start = int(emote_markers.split('-')[0])
                emote_end = int(emote_markers.split('-')[1]) + 1
                emote_word = message['msg_text'][emote_start:emote_end]
                emote_list.append((emote_word, emote_url))
            # Now we replace the emote_words with the emote_urls, starting
            # with the longest
            for emote_word, emote_url in sorted(emote_list,
                                                key=lambda x: len(x[0]),
                                                reverse=True):
                message['msg_text'] = message['msg_text'].replace(emote_word,
                                                                  emote_url)
        self.logger.debug(f"chat_overlay.plugin.py:  {message}")
        await self.websocket_queue.put(json.dumps(message))

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
