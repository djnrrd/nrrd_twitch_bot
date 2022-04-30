from typing import Dict
from typing import Union
from aiohttp.web import Request, Response, FileResponse, StreamResponse
import os
from nrrd_twitch_bot import Dispatcher, BasePlugin


class ChatOverlay(BasePlugin):

    @Dispatcher.do_privmsg
    async def do_privmsg(self, msg: Dict) -> None:
        """Log the message dictionary from the dispatcher to the logger object

        :param msg: Websockets privmsg dictionary, with all tags as Key/Value
            pairs, plus the 'nickname' key, and the 'msg_text' key
        :param send_queue: The queue object to send messages back to TwitchChat
        :param logger: A Logger object
        """
        self.logger.debug(f"chat_overlay plugin: {msg}")

    async def handler(self, request: Request) \
            -> Union[Response, FileResponse, StreamResponse]:
        base_path = os.path.join(os.path.dirname(__file__), 'static')
        if request.match_info['path'] == '' or request.match_info['path'] == '/' \
                or request.match_info['path'] == 'index.html':
            return FileResponse(path=os.path.join(base_path, 'thanks.html'))
        elif request.match_info['path'] == 'thanks.js':
            header = {'Content-type': 'application/ecmascript'}
            return FileResponse(path=os.path.join(base_path, 'thanks.js'),
                                headers=header)
