"""Interact with the Twitch Helix API
"""
import asyncio
from typing import List
from logging import Logger
from basewebapi.asyncbasewebapi import AsyncBaseWebAPI
from .config import load_config


class TwitchHelix(AsyncBaseWebAPI):

    def __init__(self, client_id: str, oauth_token: str) -> None:
        super().__init__('api.twitch.tv', '', '', secure=True)
        self.headers['Client-Id'] = client_id
        self.headers['Authorization'] = f"Bearer {oauth_token}"

    async def get_emote_set(self, emote_set_id: str) -> List:
        """Get an emote set from the Twitch Helix API

        :param emote_set_id: The ID of the emote set
        :return: A list of Emotes
        """
        path = '/helix/chat/emotes/set'
        params = {'emote_set_id': str(emote_set_id)}
        result = await self._transaction('get', path, params=params)
        return result.get('data')


async def get_emote_sets(emote_set_ids: List[str], logger: Logger) -> List:
    """Get an emote set from the Twitch Helix API

    :param emote_set_ids: The IDs of the emote sets
    :param logger: A logger object
    :return: A list of Emotes
    """
    config = load_config(logger)
    oauth_token = config['twitch']['oauth_token']
    client_id = config['twitch']['client_id']
    async with TwitchHelix(client_id, oauth_token) as twitch:
        futures = [twitch.get_emote_set(x) for x in emote_set_ids]
        emote_sets = await asyncio.gather(*futures)
    return emote_sets
