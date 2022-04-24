from aiohttp.web import Request, Response


async def handler(request: Request) -> Response:
    return Response(text=f"OK: {request.match_info['path']}")
