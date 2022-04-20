"""Manage getting Oauth tokens from Twitch
"""
import json
import os
import threading
import tkinter as tk
import webbrowser
from functools import partial
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode
from conf.twitch import CLIENT_ID


def get_twitch_oauth_token(oauth_label: tk.StringVar) -> None:
    """Launch a web browser and web server to start the Twitch OAuth process
    and receive the returned token

    :param oauth_label: The TK StringVar object that stores the OAuth Token
        value
    """
    launch_browser()
    start_web_server_thread(oauth_label)


def launch_browser() -> None:
    """Launch the user's web browser and take them to the Twitch OAuth page.
    """
    base_url = 'https://id.twitch.tv/oauth2/authorize'
    params = {'client_id': CLIENT_ID, 'redirect_uri': 'http://localhost:8000',
              'response_type': 'token',
              'scope': 'channel:moderate chat:edit chat:read '
                       'channel_commercial channel_editor'}
    url_params = urlencode(params)
    url = f"{base_url}?{url_params}"
    # Placeholder while building. don't want to hammer Twitch
    # url = 'http://localhost:8000/'
    webbrowser.open_new_tab(url)


def start_web_server_thread(oauth_label: tk.StringVar) -> None:
    """Launch the Web Server in a separate thread to wait for the response
    from Twitch

    :param oauth_label: The TK StringVar object that stores the OAuth Token
        value
    """
    start_server = partial(start_web_server, oauth_label)
    httpd = threading.Thread(target=start_server)
    httpd.daemon = True
    httpd.start()


def start_web_server(oauth_label: tk.StringVar) -> None:
    """Start a web server using a custom response handler which will
    have a reference to the controller app to return the values from twitch.

    :param oauth_label: The TK StringVar object that stores the OAuth Token
        value
    """
    # Use partial to add custom arguments to the TwitchResponseHandler
    handler = partial(TwitchResponseHandler, oauth_label)
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, handler)
    httpd.serve_forever()


class TwitchResponseHandler(BaseHTTPRequestHandler):
    """Local web server handler to handle the return request from the Twitch
    authentication portal.  Normally the __init__ method would not be
    overridden, but we need to reference the TK Label to update the value

    :param oauth_label: The TK StringVar object that stores the OAuth Token
        value
    :param *args: List of arguments accepted by BaseHTTPRequestHandler
    :param **kwargs: Dictionary of keyword arguments accepted by
        BaseHTTPRequestHandler
    """

    def __init__(self, oauth_label: tk.StringVar, *args, **kwargs):
        self.oauth_label = oauth_label
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        """GET only serves 2 files, thanks.html and thanks.js. As the twitch
        response is in the document hash, it's easier to get through
        Javascript
        """
        base_dir = os.path.dirname(__file__)
        self.send_response(200)
        file = 'static/thanks.js' if self.path == '/thanks.js' \
            else 'static/thanks.html'
        content_type = 'application/ecmascript' if self.path == '/thanks.js' \
            else 'text/html'
        with open(os.path.join(base_dir, file), 'r') as f:
            html = f.read()
        self.send_header('Content-type', content_type)
        self.end_headers()
        self.wfile.write(html.encode())

    def do_POST(self) -> None:
        """Receive the Twitch tokens via a POST from thanks.js. Update the
        original setup app with the values received and shut down the web
        server"""
        # Read the POST body and convert from JSON to a dict.
        data_string = self.rfile.read(int(self.headers['Content-Length']))
        new_object = json.loads(data_string.decode('utf-8'))
        # Send headers
        self.send_response(202)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        # Pass the twitch object back to the setup app and shut down the server
        self.oauth_label.set(new_object.get('#access_token'))
        safe_shut = threading.Thread(target=self.server.shutdown)
        safe_shut.daemon = True
        safe_shut.start()
