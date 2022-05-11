"""Entry point for the application
"""
from typing import Type, Union
import argparse
import pathlib
from .lib.tk import TwitchBotLogApp
from .lib.logger import setup_logger
from .run import run_async_tasks


def _add_args() -> argparse.ArgumentParser:
    """Set up the script arguments using argparser

    :return: The argparse parser object
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        default=False, help='Switch debugging on')
    parser.add_argument('-c', '--console-only', dest='console',
                        action='store_true', default=False,
                        help='run in console only mode')
    parser.add_argument('-l', '--log-file', dest='log_file',
                        type=pathlib.Path,
                        help='File path to output the logs to')
    return parser


def run_tk(debug: bool, log_file_path: Union[Type[pathlib.Path], None]) -> None:
    """Run the app as a TK app

    :param debug: If logging should be set to debug level
    :param log_file_path: The file path to use if logging should go to a file
    """
    app = TwitchBotLogApp(debug, log_file_path)
    app.mainloop()


def run_console(debug: bool, log_file_path: Union[Type[pathlib.Path], None]) \
        -> None:
    """

    :param debug:
    :param log_file_path:
    """
    logger = setup_logger(debug, file_path=log_file_path)
    logger.info('cli_entry.py: Starting services in console mode')
    run_async_tasks(logger)


def main() -> None:
    """Run the main TK application
    """
    parser = _add_args()
    arg = parser.parse_args()
    if arg.console:
        run_console(arg.debug, arg.log_file)
    else:
        run_tk(arg.debug, arg.log_file)


if __name__ == '__main__':
    main()
