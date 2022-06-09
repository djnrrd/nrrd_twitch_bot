"""An example plugin to provide a basic chat commands bot
"""
from typing import Dict, Union
from logging import Logger
import os
import asyncio
import sqlite3
from appdirs import user_data_dir
from nrrd_twitch_bot import BasePlugin


class ChatCommands(BasePlugin):
    """A basic chat command bot
    """

    def __init__(self, logger: Logger):
        super().__init__(logger)
        self.db_conn = self._init_db()

    async def do_privmsg(self, message: Dict) -> None:
        """Log the message dictionary from the dispatcher to the logger object

        :param message: Websockets privmsg dictionary, with all tags as
            Key/Value pairs, plus the 'nickname' key, and the 'msg_text' key
        """
        # Make sure this is a command before any further processing
        if message['msg_text'][0] != '!':
            return
        parts = message['msg_text'].split(' ')
        command = parts[0][1:]
        args = parts[1:]
        self.logger.debug(f"chat_commands: command {command} received with "
                          f"args {args}")
        response = self.chat_commands(command, *args)
        if response:
            self.logger.debug(f"chat_commands: response is {response}")
            asyncio.create_task(self.dispatcher.chat_send(response))

    def _init_db(self) -> sqlite3.Connection:
        """Load and initialise the chat_commands sqlite3 Database

        :return: The Database connection
        """
        db_dir = user_data_dir('nrrd-twitch-bot', 'djnrrd')
        db_path = os.path.join(db_dir, 'chat_commands.db')
        self.logger.debug(f"chat_commands: Loading sqlite3 dB from {db_path}")
        load_db = sqlite3.connect(db_path)
        with load_db:
            init_table = '''CREATE TABLE IF NOT EXISTS chat_commands (
                                command TEXT NOT NULL,
                                response TEXT NOT NULL);'''
            init_index = '''CREATE UNIQUE INDEX IF NOT EXISTS command_idx 
                            ON chat_commands(command);'''

            load_db.execute(init_table)
            load_db.execute(init_index)
        return load_db

    def chat_commands(self, command: str, *args) -> Union[str, None]:
        """Return the response to the chat commands

        :param command: the extracted command
        :return: The command response if found
        """
        with self.db_conn as con:
            response = con.execute('SELECT response FROM chat_commands WHERE '
                                   'command = ?', (command, ))
            result = response.fetchall()
            if len(result) == 1:
                self.logger.debug(f"chat_commands: Found entry for {command} "
                                  f"in sqlite3 dB")
                return result[0][0].format(*args)
