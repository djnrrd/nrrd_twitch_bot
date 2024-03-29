"""An example plugin to provide a basic chat commands bot
"""
from typing import Dict, Union, List
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
        user_levels = ['broadcaster', 'moderator', 'vip', 'subscriber', 'all']
        if 'broadcaster' in message['badges']:
            pass
        elif message['mod'] == '1':
            user_levels = user_levels[1:]
        elif 'vip' in message['badges']:
            user_levels = user_levels[2:]
        elif message['subscriber'] == '1':
            user_levels = user_levels[3:]
        else:
            user_levels = user_levels[4:]
        parts = message['msg_text'].split(' ')
        command = parts[0][1:]
        args = parts[1:]
        self.logger.debug(f"chat_commands: command {command} received with "
                          f"args {args}")
        if command == 'command':
            response = self.manage_commands(user_levels, *args)
        else:
            response = self.lookup_commands(command, user_levels, *args)
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
                                level TEXT NOT NULL,
                                response TEXT NOT NULL);'''
            init_index = '''CREATE UNIQUE INDEX IF NOT EXISTS command_idx 
                            ON chat_commands(command);'''

            load_db.execute(init_table)
            load_db.execute(init_index)
        return load_db

    def lookup_commands(self, command: str, user_levels: List, *args) \
            -> Union[str, None]:
        """Return the response to the chat commands

        :param command: The extracted command
        :param user_levels: The user's user levels
        :param args: The list of arguments
        :return: The command response if found
        """
        with self.db_conn as con:
            response = con.execute('SELECT response, level FROM chat_commands '
                                   'WHERE command = ?', (command, ))
            result = response.fetchall()
            if len(result) == 1:
                level = result[0][1]
                if level not in user_levels:
                    return
                self.logger.debug(f"chat_commands: Found entry for {command} "
                                  f"in sqlite3 dB")
                return result[0][0].format(*args)

    def manage_commands(self, user_levels: List, *args) -> Union[str, None]:
        """Add or delete commands to the database

        :param user_levels: The user's user levels
        :param args: The list of arguments to the 'command' command
        :return: The command response
        """
        all_levels = ['broadcaster', 'moderator', 'vip', 'subscriber', 'all']
        usage = 'Usage: !command add|delete command_name ' \
                'broadcaster|moderator|vip|subscriber|all {response}'
        if 'moderator' not in user_levels:
            return 'Mod use only'
        if len(args) >= 2:
            if args[0] == 'add':
                if len(args) >= 4:
                    command = args[1]
                    level = args[2]
                    if level not in all_levels:
                        return usage
                    response = ' '.join(args[3:])
                    with self.db_conn as con:
                        con.execute('INSERT INTO chat_commands '
                                    'VALUES (?, ?, ?);',
                                    (command, level, response))
                    return f"Added command {command}"
            elif args[0] == 'delete':
                command = args[1]
                with self.db_conn as con:
                    con.execute('DELETE FROM chat_commands WHERE command = ?;',
                                (command, ))
                return f"Deleted command {command}"
        return usage
