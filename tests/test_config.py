from unittest import TestCase
import os
import logging
from appdirs import user_config_dir
from lib.config import load_config, save_config, check_config_dir


class TestConfigs(TestCase):

    def setUp(self):
        self.logger = logging.getLogger('config_test')
        self.config_file_backup = self.file_backup()

    def tearDown(self):
        if self.config_file_backup:
            self.file_restore()

    @staticmethod
    def file_backup():
        config_dir = user_config_dir('nrrd-twitch-bot', 'djnrrd')
        config_file = os.path.join(config_dir, 'nrrd-twitch-bot.ini')
        if os.path.isfile(config_file):
            with open(config_file, 'r') as f:
                ret_file = f.read()
            return ret_file
        return None

    def file_restore(self):
        config_dir = check_config_dir(self.logger)
        config_file = os.path.join(config_dir, 'nrrd-twitch-bot.ini')
        with open(config_file, 'w') as f:
            f.write(self.config_file_backup)

    @staticmethod
    def delete_files():
        config_dir = user_config_dir('nrrd-twitch-bot', 'djnrrd')
        config_file = os.path.join(config_dir, 'nrrd-twitch-bot.ini')
        author_dir = os.path.join(user_config_dir(), 'djnrrd')
        os.remove(config_file)
        os.rmdir(config_dir)
        os.rmdir(author_dir)

    def test_load_conf(self):
        config = load_config(self.logger)
        self.assertTrue(config.has_section('twitch'))
        self.assertTrue(config.has_option('twitch', 'oauth_token'))
        self.assertTrue(config.has_option('twitch', 'channel'))

    def test_default_conf(self):
        self.delete_files()
        config_dir = user_config_dir('nrrd-twitch-bot', 'djnrrd')
        config_file = os.path.join(config_dir, 'nrrd-twitch-bot.ini')
        author_dir = os.path.join(user_config_dir(), 'djnrrd')
        config = load_config(self.logger)
        self.assertTrue(config.has_section('twitch'))
        self.assertTrue(config.has_option('twitch', 'oauth_token'))
        self.assertTrue(config.has_option('twitch', 'channel'))
        self.assertEqual(config.get('twitch', 'oauth_token'), 'N/A')
        self.assertEqual(config.get('twitch', 'channel'), 'N/A')
        self.assertTrue(os.path.isfile(config_file))
        self.assertTrue(os.path.isdir(config_dir))
        self.assertTrue(os.path.isdir(author_dir))
