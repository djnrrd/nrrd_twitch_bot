"""Entry point for the application
"""
import argparse
from .lib.tk import TwitchBotLogApp


def _add_args() -> argparse.ArgumentParser:
    """Set up the script arguments using argparser

    :return: The argparse parser object
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        default=False, help='Switch debugging on')
    return parser


def main() -> None:
    """Run the main TK application
    """
    parser = _add_args()
    arg = parser.parse_args()
    app = TwitchBotLogApp(arg.debug)
    app.after(0, app.launch_sockets)
    app.mainloop()


if __name__ == '__main__':
    main()
