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
        self.logger.debug(f"chat_overlay plugin: {message}")
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
            return FileResponse(path=os.path.join(base_path, 'thanks.html'))
        if request.match_info['path'] == 'thanks.js':
            header = {'Content-type': 'application/ecmascript'}
            return FileResponse(path=os.path.join(base_path, 'thanks.js'),
                                headers=header)

    async def websocket_handler(self, request: Request) -> WebSocketResponse:
        """Create a websocket instance for the plugin

        :param request: An aiohttp Request object
        :return: The WebSocket response
        """
        return await self._websocket_handler(request)
