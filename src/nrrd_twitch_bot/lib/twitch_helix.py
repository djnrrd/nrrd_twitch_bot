"""Interact with the Twitch Helix API
"""
import asyncio
from typing import List
from logging import Logger
from basewebapi.asyncbasewebapi import AsyncBaseWebAPI
from .config import load_default_config


class TwitchHelix(AsyncBaseWebAPI):
    """Connect to the Twitch Helix API

    This should be used with the Asynchronous context manager

    :param client_id: Twitch Client ID string
    :param oauth_token: Twitch OAUTH token
    """

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

    async def get_global_badges(self) -> List:
        """Get the global chat badges from the Titch Helix API

        :return: A list of badges
        """
        path ='/helix/chat/badges/global'
        result = await self._transaction('get', path)
        return result.get('data')

    async def get_channel_badges(self, broadcaster_id: str) -> List:
        """Get the chat badges for a specific channel

        :param broadcaster_id: The ID for the channel
        :return: A list of badges
        """
        path = '/helix/chat/badges/'
        params = {'broadcaster_id': broadcaster_id}
        result = await self._transaction('get', path, params=params)
        return result.get('data')


async def get_emote_sets(emote_set_ids: List[str], logger: Logger) -> List:
    """Get an emote set from the Twitch Helix API

    :param emote_set_ids: The IDs of the emote sets
    :param logger: A logger object
    :return: A list of Emotes
    """
    config = load_default_config(logger)
    oauth_token = config['twitch']['oauth_token']
    client_id = config['twitch']['client_id']
    async with TwitchHelix(client_id, oauth_token) as twitch:
        emote_sets = []
        start_mark = 0
        # Make sure we don't fall foul of rate limiting by doing 10 requests
        # at a time
        for end_mark in range(10, len(emote_set_ids), 10):
            futures = [twitch.get_emote_set(x) for x in
                       emote_set_ids[start_mark:end_mark]]
            emote_sets += await asyncio.gather(*futures)
            start_mark = end_mark
        # And the last one(s)
        futures = [twitch.get_emote_set(x) for x in
                   emote_set_ids[start_mark:]]
        emote_sets += await asyncio.gather(*futures)
    return emote_sets


async def get_channel_badges(broadcaster_id: str, logger: Logger) -> List:
    """Get global and channel badges from the Twitch Helix API

    :param broadcaster_id: The ID for the channel
    :param logger: A logger object
    :return: A list of Badges
    """
    config = load_default_config(logger)
    oauth_token = config['twitch']['oauth_token']
    client_id = config['twitch']['client_id']
    async with TwitchHelix(client_id, oauth_token) as twitch:
        badge_list = twitch.get_global_badges()
        badge_list += twitch.get_channel_badges(broadcaster_id)
    return badge_list
