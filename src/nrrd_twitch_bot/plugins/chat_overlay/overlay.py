from typing import Union
from aiohttp.web import Request, Response, FileResponse, StreamResponse
import os


async def handler(request: Request) \
        -> Union[Response, FileResponse, StreamResponse]:
    base_path = os.path.join(os.path.dirname(__file__), 'static')
    if request.match_info['path'] == '' or request.match_info['path'] == '/' \
            or request.match_info['path'] == 'index.html':
        return FileResponse(path=os.path.join(base_path, 'thanks.html'))
    elif request.match_info['path'] == 'thanks.js':
        header = {'Content-type': 'application/ecmascript'}
        return FileResponse(path=os.path.join(base_path, 'thanks.js'),
                            headers=header)
