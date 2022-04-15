"""A module for getting the OAUTH token from Twitch
"""
import logging
from basewebapi.asyncbasewebapi import AsyncBaseWebAPI


class AsyncTwitchIDAPI(AsyncBaseWebAPI):
    """A very basic asynchronous wrapper to get the OAuth token
    :param client_id: Twitch Client ID
    :param client_secret: Twitch Client Secret
    """

    def __init__(self, client_id: str, client_secret: str,
                 logger: logging.Logger = None) -> None:
        super().__init__('id.twitch.tv', '', '', secure=True)
        self.client_id = client_id
        self.client_secret = client_secret
        self.headers['Accept'] = 'application/json'
        if not logger:
            self.logger = logging.getLogger()
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger = logger

    async def get_oauth_token(self) -> str:
        """Get the OAuth token required for IGDB

        :return: The OAuth token
        """
        self.logger.debug('Getting Twitch OAUTH Token')
        path = '/oauth2/token'
        params = {'client_id': self.client_id,
                  'client_secret': self.client_secret,
                  'grant_type': 'client_credentials'}
        response = await self._transaction('post', path, params=params)
        self.logger.debug(f"Received {response} from Twitch API")
        return response['access_token']
