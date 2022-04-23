from typing import List
from types import ModuleType
from logging import Logger
import os
import sys
import importlib
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


def _load_plugins(plugin_module: str, logger: Logger) -> List[ModuleType]:
    """load all plugin objects

    :param logger: A logger object
    :return: A list of imported packages from the list of plugins
    """
    local_plugin_path = os.path.join(os.path.dirname(__file__), '..',
                                     'plugins')
    sys.path.extend([local_plugin_path])
    plugins = _load_from_config(logger)
    return [importlib.import_module(plugin_module, x) for x in plugins
            if importlib.util.find_spec(plugin_module, x)]


def load_dispatchers(logger: Logger) -> List[ModuleType]:
    """Load the plugins and return those that want to use the dispatcher

    :return: A list of dispatcher plugins
    """
    return _load_plugins('.dispatcher', logger)
