from typing import Dict
from basewebapi.asyncbasewebapi import AsyncBaseWebAPI


class AsyncBttv(AsyncBaseWebAPI):
    """A class for getting emotes from BTTV
    """

    def __init__(self):
        super().__init__('api.betterttv.net', '', '', secure=True)
        self.headers['Accept'] = 'application/json'

    async def get_channel_emotes(self, channel_id: str) -> Dict:
        """Get the BTTV emotes for a channel

        :param channel_id: The channel ID
        :return: The dictionary of channel details and emotes.
        """
        path = f"/3/cached/users/twitch/{channel_id}"
        results = await self._transaction('get', path)
        return results
