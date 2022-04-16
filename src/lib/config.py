"""Config file management
"""
from logging import Logger
import os
from configparser import ConfigParser
from appdirs import user_config_dir


def check_config_dir(logger: Logger) -> str:
    """Check if the config directories exist and create them if not.

    :param logger: A Logger object
    :return: The path the config directory
    """
    config_dir = user_config_dir('nrrd-twitch-bot', 'djnrrd')
    if not os.path.isdir(config_dir):
        logger.debug('No config directory found, creating one')
        # On Windows appdirs always have to be %AppDir%//author//appname so
        # we have to create the author folder first, which would end up being
        # empty on linux systems
        author_dir = os.path.join(user_config_dir(), 'djnrrd')
        if not os.path.isdir(author_dir):
            logger.debug(f"Creating author directory: {author_dir}")
            os.mkdir(author_dir)
        logger.debug(f"Creating application directory: {config_dir}")
        os.mkdir(config_dir)
    return config_dir


def config_defaults(config: ConfigParser, logger: Logger) -> ConfigParser:
    """Seed the config file with default values and save the file to disk

    :param config: An empty ConfigParser object
    :param logger: A Logger object
    :return: A ConfigParser object with default values
    """
    logger.debug('Adding default values to config file')
    config.add_section('twitch')
    config['twitch']['oauth_token'] = 'N/A'
    config['twitch']['channel'] = 'N/A'
    save_config(config, logger)
    return config


def load_config(logger: Logger) -> ConfigParser:
    """Load the config file and return the ConfigParser object.

    If no config file is present the ConfigParser object would be "empty"
    and this should be checked outside of this function to load defaults into
    the ConfigParser object.

    :param logger: A Logger object
    :return: the ConfigParser object
    """
    config = ConfigParser()
    # Check the config directory exists and create if needbe
    config_dir = check_config_dir(logger)
    config_file = os.path.join(config_dir, 'nrrd-twitch-bot.ini')
    if not os.path.isfile(config_file):
        logger.debug(f"Config file {config_file} does not exist")
        config = config_defaults(config, logger)
    else:
        config.read(config_file)
    return config


def save_config(config: ConfigParser, logger: Logger) -> None:
    """Save the config file to the user's local config directory.

    :param config: The ConfigParser object
    :param logger: A Logger object
    """
    config_dir = check_config_dir(logger)
    config_file = os.path.join(config_dir, 'nrrd-twitch-bot.ini')
    logger.debug(f"Saving config file: {config_file}")
    with open(config_file, 'w') as f:
        config.write(f)
