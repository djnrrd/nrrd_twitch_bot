"""Load plugins from the config file and import them
"""
from typing import List
from types import ModuleType
from logging import Logger
import os
import sys
import importlib
import importlib.util
from appdirs import user_data_dir
from .config import load_config


def _load_from_config(logger: Logger) -> List[str]:
    """Load the list of plugin names from the config file

    :param logger: A logger object
    :return: The list of plugin names
    """
    logger.debug('Loading plugin list')
    config = load_config(logger)
    plugins = config['plugins']['plugins']
    logger.debug(f"plugins list: {plugins}")
    return plugins.split(':')


def _update_paths(logger: Logger) -> None:
    """Update the sys path with the plugin locations

    :param logger:
    """
    logger.debug('Adding local plugin path')
    local_plugin_path = os.path.join(os.path.dirname(__file__), '..', 'plugins')
    user_plugin_path = os.path.join(user_data_dir('nrrd-twitch-bot', 'djnrrd'),
                                    'plugins')
    if not os.path.isdir(user_plugin_path):
        logger.debug('No plugin directory found, creating one')
        # On Windows appdirs always have to be %AppDir%//author//appname so
        # we have to create the author folder first, which would end up being
        # empty on linux systems
        author_dir = os.path.join(user_data_dir(), 'djnrrd')
        if not os.path.isdir(author_dir):
            logger.debug(f"Creating author directory: {author_dir}")
            os.mkdir(author_dir)
        app_dir = user_data_dir('nrrd-twitch-bot', 'djnrrd')
        if not os.path.isdir(app_dir):
            logger.debug(f"Creating application directory: {app_dir}")
            os.mkdir(app_dir)
        logger.debug(f"Creating plugin directory: {user_plugin_path}")
        os.mkdir(user_plugin_path)
    sys.path.extend([local_plugin_path, user_plugin_path])


def _load_plugins(plugin_module: str, logger: Logger) -> List[ModuleType]:
    """load all plugin objects

    :param logger: A logger object
    :return: A list of imported packages from the list of plugins
    """
    _update_paths(logger)
    plugins = _load_from_config(logger)
    logger.debug(f"Importing plugin libraries supporting {plugin_module}")
    modules = [importlib.import_module(plugin_module, x) for x in plugins
               if importlib.util.find_spec(plugin_module, x)]
    logger.debug(f"Loaded modules {[str(x) for x in modules]}")
    return modules


def load_dispatchers(logger: Logger) -> List[ModuleType]:
    """Load the plugins and return those that want to use the dispatcher

    :return: A list of dispatcher plugins
    """
    logger.debug('Loading dispatcher plugin modules')
    return _load_plugins('.dispatcher', logger)
